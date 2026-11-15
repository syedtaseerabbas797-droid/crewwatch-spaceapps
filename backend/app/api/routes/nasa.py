from fastapi import APIRouter
from app.integrations.nasa_client import (
    get_solar_flares,
    get_radiation_multiplier,
    get_epic_image,
    get_apod,
    get_neo_feed,
)

router = APIRouter(prefix="/api/nasa", tags=["NASA Open APIs"])

@router.get("/space-weather")
async def nasa_space_weather():
    flares = await get_solar_flares()
    multiplier = await get_radiation_multiplier()
    return {
        "status": "connected",
        "source": "NASA Space Weather Database Of Notifications, Knowledge, Information (DONKI)",
        "solar_flares_count": len(flares),
        "recent_flares": flares[:5],
        "radiation_multiplier": multiplier,
        "impact_description": (
            "Elevated radiation environment actively driving CrewWatch telemetry simulation."
            if multiplier > 1.0 else "Quiet solar conditions: baseline radiation profile."
        )
    }

@router.get("/epic-image")
async def nasa_epic():
    data = await get_epic_image()
    return {
        "source": "NASA Earth Polychromatic Imaging Camera (EPIC) / DSCOVR Satellite",
        "data": data,
    }

@router.get("/apod")
async def nasa_apod():
    data = await get_apod()
    return {
        "source": "NASA Astronomy Picture of the Day (APOD)",
        "data": data,
    }

@router.get("/near-earth-objects")
async def nasa_neo():
    data = await get_neo_feed()
    return {
        "source": "NASA Near Earth Object Web Service (NeoWs)",
        "data": data,
    }
