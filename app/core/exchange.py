import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.redis_client import get_redis

CACHE_KEY = "exchange:USD-BRL"


async def get_usd_to_brl_rate() -> float:
    redis = await get_redis()
    cached = await redis.get(CACHE_KEY)
    if cached is not None:
        return float(cached)

    rate = await _fetch_from_awesomeapi()
    if rate is None:
        rate = await _fetch_from_frankfurter()
    if rate is None:
        raise HTTPException(status_code=503, detail="Serviço de câmbio indisponível")

    await redis.setex(CACHE_KEY, settings.exchange_cache_ttl, str(rate))
    return rate


async def _fetch_from_awesomeapi() -> float | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.exchange_api_primary)
            response.raise_for_status()
            data = response.json()
            return float(data["USDBRL"]["bid"])
    except Exception:
        return None


async def _fetch_from_frankfurter() -> float | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.exchange_api_fallback)
            response.raise_for_status()
            data = response.json()
            return float(data["rates"]["BRL"])
    except Exception:
        return None
