import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    ssl=True,
    decode_responses=True
)