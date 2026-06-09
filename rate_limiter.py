from redis_config import (
    redis_client
)

from config import (
    RATE_LIMIT_WINDOW
)


def check_rate_limit(
    key,
    limit
):

    current = redis_client.get(key)

    if current:

        current = int(current)

        if current >= limit:

            return False

        redis_client.incr(key)

        return True

    redis_client.setex(
        key,
        RATE_LIMIT_WINDOW,
        1
    )

    return True