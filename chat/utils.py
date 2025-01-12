import aioredis
import asyncio

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
                await asyncio.sleep(2 ** retries)
        raise aioredis.ConnectionError("Failed to connect to Redis after multiple retries.")

    async def set(self, key, value, timeout=None):
        if timeout:
            await self.redis.setex(key, timeout, value)
        else:
            await self.redis.set(key, value)

    async def get(self, key):
        value = await self.redis.get(key)
        return value

    async def delete(self, key):
        await self.redis.delete(key)

    async def increment(self, key, amount=1):
        return await self.redis.incrby(key, amount)

    async def publish(self, channel, message):
        await self.redis.publish(channel, message)

    async def keys(self, pattern="*"):
        return await self.redis.keys(pattern)

    async def flushdb(self):
        await self.redis.flushdb()
