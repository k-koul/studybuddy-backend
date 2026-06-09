from passlib.context import CryptContext
from jose import jwt
from config import SECRET_KEY
from rate_limiter import check_rate_limit
from config import LOGIN_RATE_LIMIT
from database import get_connection
from fastapi import HTTPException
from logger_config import logger

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ---------------- REGISTER SERVICE ----------------

def register_user(user):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (user.email,)
        )

        existing = cursor.fetchone()

        if existing:

            cursor.close()
            conn.close()

            logger.warning(
                f"Registration attempted with existing email: {user.email}"
            )

            return {
                "success": True,
                "data": {
                    "message": "Email already registered"
                }
            }

        hashed_password = pwd_context.hash(
            user.password
        )

        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (user.email, hashed_password)
        )

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(
            f"User registered: {user.email}"
        )

        return {
            "success": True,
            "data": {
                "message": "User registered successfully"
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Register Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------- LOGIN SERVICE ----------------

def login_user(user):

    rate_key = f"login:{user.email}"

    allowed = check_rate_limit(
        rate_key,
        LOGIN_RATE_LIMIT
    )

    if not allowed:

        logger.warning(
            f"Login rate limit hit: {user.email}"
        )

        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later."
        )

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT email, password FROM users WHERE email = %s",
            (user.email,)
        )

        db_user = cursor.fetchone()

        cursor.close()
        conn.close()

        if db_user:

            password_correct = pwd_context.verify(
                user.password,
                db_user[1]
            )

            if password_correct:

                logger.info(
                    f"User logged in: {user.email}"
                )

                token = jwt.encode(
                    {"email": user.email},
                    SECRET_KEY,
                    algorithm="HS256"
                )

                return {
                    "success": True,
                    "data": {
                        "token": token
                    }
                }

        logger.warning(
            f"Failed login attempt: {user.email}"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Login Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )