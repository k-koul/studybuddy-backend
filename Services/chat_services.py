import google.generativeai as genai

from redis_config import redis_client

from rate_limiter import check_rate_limit

from database import get_connection

from config import (
    GEMINI_API_KEY,
    MODEL_NAME,
    CACHE_EXPIRY,
    CHAT_RATE_LIMIT
)

from fastapi import HTTPException

from logger_config import logger

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(MODEL_NAME)


def create_session(user_email, title):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO chat_sessions (user_email, title)
            VALUES (%s, %s) RETURNING id
            """,
            (user_email, title)
        )

        session_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(
            f"Session created: {user_email}"
        )

        return {
            "success": True,
            "data": {
                "session_id": session_id
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Create Session Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def rename_session(session_id, user_email, new_title):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE chat_sessions
            SET title = %s
            WHERE id = %s AND user_email = %s
            """,
            (new_title, session_id, user_email)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return {  
            "success": True,
            "data": {
                "message": "Renamed successfully"
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Rename Session Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def save_message(session_id, role, text):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_messages (session_id, role, text)
        VALUES (%s, %s, %s)
        """,
        (session_id, role, text)
    )

    conn.commit()
    cursor.close()
    conn.close()


def update_session_title(session_id, title):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE chat_sessions
        SET title = %s
        WHERE id = %s
        """,
        (title, session_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_sessions(user_email):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, title, created_at
            FROM chat_sessions
            WHERE user_email = %s
            ORDER BY created_at DESC
            """,
            (user_email,)
        )

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "data": [
                {
                    "id": row[0],
                    "title": row[1],
                    "created_at": str(row[2])
                }
                for row in rows
            ]
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Get Sessions Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def get_messages(session_id):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, text
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at ASC
            """,
            (session_id,)
        )

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "data": [
                {
                    "role": row[0],
                    "text": row[1]
                }
                for row in rows
            ]
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Get Messages Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def delete_session(session_id, user_email):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM chat_sessions
            WHERE id = %s AND user_email = %s
            """,
            (session_id, user_email)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "data": {
                "message": "Deleted successfully"
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Delete Session Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def chat_with_ai(
    message: str,
    user_email: str,
    session_id: int,
    is_first: bool
):

    rate_key = f"chat:{user_email}"

    allowed = check_rate_limit(
        rate_key,
        CHAT_RATE_LIMIT
    )

    if not allowed:

        logger.warning(
            f"Chat rate limit hit: {user_email}"
        )

        raise HTTPException(
            status_code=429,
            detail="Chat rate limit exceeded. Please wait."
        )

    try:

        if is_first:

            title = message[:50]

            update_session_title(
                session_id,
                title
            )

        cache_key = f"chat_msg:{message}"

        cached = redis_client.get(cache_key)

        if cached:

            logger.info(
                f"Chat cache hit: {message}"
            )

            save_message(
                session_id,
                "user",
                message
            )

            save_message(
                session_id,
                "bot",
                cached
            )

            return {
                "success": True,
                "data": {
                    "message": message,
                    "reply": cached,
                    "source": "cache"
                }
            }

        logger.info(
            f"Chat Gemini call: {message}"
        )

        save_message(
            session_id,
            "user",
            message
        )

        response = model.generate_content(
            message
        )

        save_message(
            session_id,
            "bot",
            response.text
        )

        redis_client.setex(
            cache_key,
            CACHE_EXPIRY,
            response.text
        )

        return {
            "success": True,
            "data": {
                "message": message,
                "reply": response.text,
                "source": "gemini"
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Chat Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )