from dotenv import load_dotenv

import os

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

SECRET_KEY = os.getenv(
    "SECRET_KEY"
)

MODEL_NAME = os.getenv(
    "MODEL_NAME"
)

CHUNK_SIZE = int(
    os.getenv("CHUNK_SIZE")
)

CHUNK_OVERLAP = int(
    os.getenv("CHUNK_OVERLAP")
)

FRONTEND_URL = os.getenv(
    "FRONTEND_URL"
)

REDIS_HOST = os.getenv(
    "REDIS_HOST"
)

REDIS_PORT = int(
    os.getenv("REDIS_PORT")
)

CACHE_EXPIRY = int(
    os.getenv("CACHE_EXPIRY")
)

LOGIN_RATE_LIMIT = int(
    os.getenv("LOGIN_RATE_LIMIT")
)

ASK_RATE_LIMIT = int(
    os.getenv("ASK_RATE_LIMIT")
)

RATE_LIMIT_WINDOW = int(
    os.getenv("RATE_LIMIT_WINDOW")
)

CHAT_RATE_LIMIT = int(
    os.getenv("CHAT_RATE_LIMIT")
)

DB_URL = os.getenv(
    "DB_URL"
)