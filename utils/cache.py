from typing import Any, Optional
import aioredis
import json
from datetime import datetime, timedelta
import pickle

class Cache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        # Separate connection for binary data (images)
        self.binary_redis = aioredis.from_url(
            redis_url,
            encoding=None,
            decode_responses=False
        )

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: int = 3600
    ) -> bool:
        """Set value in cache with expiration in seconds."""
        try:
            data = json.dumps(value)
            await self.redis.set(key, data, ex=expire)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def get_binary(self, key: str) -> Optional[bytes]:
        """Get binary data (images) from cache."""
        try:
            return await self.binary_redis.get(f"bin:{key}")
        except Exception as e:
            print(f"Cache get_binary error: {e}")
            return None

    async def set_binary(
        self, 
        key: str, 
        value: bytes, 
        expire: int = 3600
    ) -> bool:
        """Set binary data (images) in cache."""
        try:
            await self.binary_redis.set(f"bin:{key}", value, ex=expire)
            return True
        except Exception as e:
            print(f"Cache set_binary error: {e}")
            return False

    async def get_hash(self, key: str) -> Optional[dict]:
        """Get hash from cache."""
        try:
            data = await self.redis.hgetall(key)
            return data if data else None
        except Exception as e:
            print(f"Cache get_hash error: {e}")
            return None

    async def set_hash(
        self, 
        key: str, 
        value: dict, 
        expire: int = 3600
    ) -> bool:
        """Set hash in cache."""
        try:
            await self.redis.hmset(key, value)
            if expire:
                await self.redis.expire(key, expire)
            return True
        except Exception as e:
            print(f"Cache set_hash error: {e}")
            return False
