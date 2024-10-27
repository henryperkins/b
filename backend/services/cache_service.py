import json
from typing import Any, Optional
from ..database.db import redis_client
from ..config import settings

class CacheService:
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        data = redis_client.get(key)
        return json.loads(data) if data else None

    @staticmethod
    async def set(key: str, value: Any, ttl: int = settings.CACHE_TTL):
        redis_client.setex(key, ttl, json.dumps(value))

    @staticmethod
    async def delete(key: str):
        redis_client.delete(key)

    @staticmethod
    async def clear_pattern(pattern: str):
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)

cache_service = CacheService()