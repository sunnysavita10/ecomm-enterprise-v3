from fastapi import HTTPException
from redis.asyncio import Redis

class UserLimiter:
    def __init__(self, redis: Redis, max_per_minute: int):
        self.redis = redis
        self.limit = max_per_minute

    async def check(self, user_id: str):
        # Redis-backed fixed window; safe across multiple API replicas.
        import time
        slot = int(time.time()) // 60
        key = f"rate:chat:{user_id}:{slot}"
        try:
            async with self.redis.pipeline(transaction=True) as pipeline:
                pipeline.incr(key)
                pipeline.expire(key, 90)
                result = await pipeline.execute()
            if int(result[0]) > self.limit:
                raise HTTPException(429, "Too many requests. Try again shortly.")
        except HTTPException:
            raise
        except Exception:
            # Fail closed: don't silently disable production rate limiting.
            raise HTTPException(503, "Rate limit service temporarily unavailable") from None
