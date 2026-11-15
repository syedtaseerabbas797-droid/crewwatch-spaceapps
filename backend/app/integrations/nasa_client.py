import httpx
import logging
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.integrations.redis_client import redis_get, redis_set

logger = logging.getLogger(__name__)

NASA_BASE_URL = "https://api.nasa.gov"

FLARE_RADIATION_MAP = {
    "A": 1.0,
    "B": 1.1,
    "C": 1.3,
    "M": 1.7,
    "X": 2.5,
}

async def _nasa_get(path: str, params: dict | None = None) -> dict | list | None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        query = {"api_key": settings.NASA_API_KEY or "DEMO_KEY"}
        if params:
            query.update(params)
        try:
            response = await client.get(f"{NASA_BASE_URL}{path}", params=query)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.warning(f"NASA API timeout on path: {path}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"NASA API error {e.response.status_code} for path: {path}")
            return None
        except Exception as e:
            logger.error(f"NASA API unexpected error: {e}")
            return None

async def get_solar_flares(days_back: int = 7) -> list[dict]:
    cache_key = "nasa:donki:flr"
    cached = await redis_get(cache_key)
    if cached and isinstance(cached, list):
        return cached

    today = datetime.now(timezone.utc)
    start = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    data = await _nasa_get("/DONKI/FLR", {"startDate": start, "endDate": end})
    if not data or not isinstance(data, list):
        return []

    await redis_set(cache_key, data, ex=900)  # Cache for 15 mins
    return data

async def get_radiation_multiplier() -> float:
    cached = await redis_get("simulator:radiation_multiplier")
    if cached is not None:
        try:
            return float(cached)
        except (ValueError, TypeError):
            pass

    flares = await get_solar_flares()
    if not flares:
        multiplier = 1.0
    else:
        worst_letter = "A"
        letter_ranks = {"A": 0, "B": 1, "C": 2, "M": 3, "X": 4}
        for flare in flares:
            flare_class = flare.get("classType", "A")
            if flare_class:
                letter = flare_class[0].upper()
                if letter in letter_ranks and letter_ranks[letter] > letter_ranks.get(worst_letter, 0):
                    worst_letter = letter
        multiplier = FLARE_RADIATION_MAP.get(worst_letter, 1.0)

    await redis_set("simulator:radiation_multiplier", str(multiplier), ex=900)
    return multiplier

async def get_epic_image() -> dict | None:
    cache_key = "nasa:epic:latest"
    cached = await redis_get(cache_key)
    if cached:
        return cached

    data = await _nasa_get("/EPIC/api/natural")
    if not data or not isinstance(data, list) or len(data) == 0:
        return {
            "image_url": "https://epic.gsfc.nasa.gov/archive/natural/2026/01/01/png/epic_1b_20260101003633.png",
            "date": "2026-01-01",
            "caption": "Earth as seen from DSCOVR satellite (Default archive view)",
            "coordinates": {"lat": 0.0, "lon": 0.0}
        }

    latest = data[0]
    image_name = latest.get("image", "")
    date_str = latest.get("date", "")[:10].replace("-", "/")
    image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{date_str}/png/{image_name}.png"

    result = {
        "image_url": image_url,
        "date": latest.get("date", "")[:10],
        "caption": latest.get("caption", "Earth as seen from DSCOVR satellite"),
        "coordinates": latest.get("centroid_coordinates", {}),
    }
    await redis_set(cache_key, result, ex=3600)
    return result

async def get_apod() -> dict | None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cache_key = f"nasa:apod:{today}"
    cached = await redis_get(cache_key)
    if cached:
        return cached

    data = await _nasa_get("/planetary/apod")
    if not data or not isinstance(data, dict):
        return {
            "title": "Cosmic Deep Space Horizon",
            "explanation": "NASA exploration telemetry background visualization.",
            "url": "https://apod.nasa.gov/apod/image/2401/rosette_goldstein_960.jpg",
            "date": today
        }

    result = {
        "title": data.get("title", ""),
        "explanation": data.get("explanation", ""),
        "url": data.get("url", ""),
        "hdurl": data.get("hdurl", ""),
        "media_type": data.get("media_type", "image"),
        "date": data.get("date", today),
    }
    await redis_set(cache_key, result, ex=86400)
    return result

async def get_neo_feed() -> dict | None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cache_key = f"nasa:neo:{today}"
    cached = await redis_get(cache_key)
    if cached:
        return cached

    data = await _nasa_get("/neo/rest/v1/feed", {"start_date": today, "end_date": today})
    if not data or not isinstance(data, dict):
        return {"element_count": 0, "hazardous_count": 0, "date": today, "objects": []}

    element_count = data.get("element_count", 0)
    neos = data.get("near_earth_objects", {}).get(today, [])
    hazardous = [n for n in neos if n.get("is_potentially_hazardous_asteroid")]

    result = {
        "element_count": element_count,
        "hazardous_count": len(hazardous),
        "date": today,
        "objects": [
            {
                "name": n.get("name"),
                "diameter_km": n.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_max"),
                "is_hazardous": n.get("is_potentially_hazardous_asteroid"),
            }
            for n in neos[:5]
        ],
    }
    await redis_set(cache_key, result, ex=3600)
    return result
