import redis
import os

# LRU eviction is set in Redis config (maxmemory-policy allkeys-lru)
# This is what makes read-heavy traffic fast — cache hit = no DB query

REDIS_CLIENT = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)

# How long a short code stays cached (1 hour)
CACHE_TTL = 3600


def get_cached_url(short_code: str) -> str | None:
    return REDIS_CLIENT.get(f"url:{short_code}")


def set_cached_url(short_code: str, original_url: str):
    REDIS_CLIENT.setex(f"url:{short_code}", CACHE_TTL, original_url)


def invalidate(short_code: str):
    REDIS_CLIENT.delete(f"url:{short_code}")