import aioredis
import asyncio
import json


class CacheUtility:
    def __init__(self, redis_url="redis://localhost:6379/0", max_retries=5):
        self.redis_url = redis_url
        self.max_retries = max_retries
        self.redis = None

    async def connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
                return
            except aioredis.ConnectionError:
                retries += 1
                await asyncio.sleep(min(2 ** retries, 5))
        raise aioredis.ConnectionError("Failed to connect to Redis after multiple retries.")

    async def close(self):
        if self.redis:
            await self.redis.close()

    async def set(self, key, value, timeout=None):
        try:
            value = json.dumps(value)
            if timeout:
                await self.redis.setex(key, timeout, value)
            else:
                await self.redis.set(key, value)
        except aioredis.ConnectionError as e:
            print(f"Redis connection error during 'set': {e}")

    async def get(self, key):
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except (aioredis.ConnectionError, json.JSONDecodeError) as e:
            print(f"Redis connection error or deserialization issue during 'get': {e}")
            return None

    async def delete(self, key):
        try:
            await self.redis.delete(key)
        except aioredis.ConnectionError as e:
            print(f"Redis connection error during 'delete': {e}")

    async def incr(self, key, amount=1):
        try:
            return await self.redis.incrby(key, amount)
        except aioredis.ConnectionError as e:
            print(f"Redis connection error during 'incr': {e}")
            return None

    async def publish(self, channel, message):
        try:
            await self.redis.publish(channel, message)
        except aioredis.ConnectionError as e:
            print(f"Redis connection error during 'publish': {e}")

    async def keys(self, pattern="*"):
        try:
            return await self.redis.keys(pattern)
        except aioredis.ConnectionError as e:
            print(f"Redis connection error during 'keys': {e}")
            return []

    async def flushdb(self):
        try:
            await self.redis.flushdb()
        except aioredis.ConnectionError as e:
            print(f"Redis connection error during 'flushdb': {e}")
