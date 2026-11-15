import json
import logging
from typing import Any
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None
_in_memory_cache: dict[str, Any] = {}

async def get_redis() -> aioredis.Redis | None:
    global _redis
    if _redis is None and settings.REDIS_URL:
        try:
            _redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
            )
            # Test connection
            await _redis.ping()
        except Exception as e:
            logger.warning(f"Could not connect to remote Redis ({e}), falling back to memory.")
            _redis = None
    return _redis

async def redis_set(key: str, value: Any, ex: int | None = None) -> bool:
    r = await get_redis()
    if r:
        try:
            data = json.dumps(value) if not isinstance(value, str) else value
            await r.set(key, data, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Redis SET failed ({e}), using memory.")
    _in_memory_cache[key] = value
    return True

async def redis_get(key: str) -> Any | None:
    r = await get_redis()
    if r:
        try:
            val = await r.get(key)
            if val is not None:
                try:
                    return json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    return val
        except Exception as e:
            logger.error(f"Redis GET failed ({e}), checking memory.")
    return _in_memory_cache.get(key)

async def redis_publish(channel: str, message: dict) -> int:
    r = await get_redis()
    if r:
        try:
            data = json.dumps(message, default=str)
            return await r.publish(channel, data)
        except Exception as e:
            logger.error(f"Redis PUBLISH failed ({e}).")
    return 1

async def close_redis():
    global _redis
    if _redis:
        try:
            await _redis.aclose()
        except Exception:
            pass
        _redis = None
