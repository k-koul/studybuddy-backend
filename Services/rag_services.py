from pypdf import PdfReader

from sentence_transformers import SentenceTransformer

import faiss

import google.generativeai as genai

from redis_config import redis_client

from database import get_connection

from config import (
    GEMINI_API_KEY,
    MODEL_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CACHE_EXPIRY
)

from rate_limiter import check_rate_limit

from config import ASK_RATE_LIMIT

from fastapi import HTTPException

from logger_config import logger

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(MODEL_NAME)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

stored_chunks = []

faiss_index = None


def save_rag_history(user_email, question, answer):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO rag_history (user_email, question, answer)
        VALUES (%s, %s, %s)
        """,
        (user_email, question, answer)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_rag_history(user_email):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, question, answer, created_at
            FROM rag_history
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
                    "question": row[1],
                    "answer": row[2],
                    "created_at": str(row[3])
                }
                for row in rows
            ]
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Get RAG History Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def delete_rag_history(entry_id, user_email):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM rag_history
            WHERE id = %s AND user_email = %s
            """,
            (entry_id, user_email)
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
            f"Delete RAG History Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def chunk_text(
    text,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP
):

    chunks = []
    i = 0

    while i < len(text):

        chunks.append(text[i:i + chunk_size])

        i += chunk_size - overlap

    return chunks


async def process_pdf(file):

    try:

        pdf = PdfReader(file.file)

        text = ""

        for page in pdf.pages:

            extracted = page.extract_text()

            if extracted:

                text += extracted

        chunks = chunk_text(text)

        global stored_chunks
        global faiss_index

        stored_chunks = chunks

        embeddings = embedding_model.encode(
            chunks
        )

        dimension = embeddings.shape[1]

        faiss_index = faiss.IndexFlatL2(
            dimension
        )

        faiss_index.add(
            embeddings
        )

        logger.info(
            f"PDF uploaded: {file.filename}"
        )

        return {
            "success": True,
            "data": {
                "filename": file.filename,
                "total_chunks": len(chunks),
                "message": "PDF uploaded successfully"
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"PDF Upload Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def ask_question(query, user_email):

    allowed = check_rate_limit(
        f"ask:{user_email}",
        ASK_RATE_LIMIT
    )

    if not allowed:

        logger.warning(
            f"RAG rate limit hit: {user_email}"
        )

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait."
        )

    try:

        global faiss_index

        if faiss_index is None:

            raise HTTPException(
                status_code=400,
                detail="Upload a PDF first"
            )

        cached_answer = redis_client.get(
            query
        )

        if cached_answer:

            logger.info(
                f"RAG cache hit: {query}"
            )

            save_rag_history(
                user_email,
                query,
                cached_answer
            )

            return {
                "success": True,
                "data": {
                    "question": query,
                    "answer": cached_answer,
                    "source": "cache"
                }
            }

        logger.info(
            f"RAG Gemini call: {query}"
        )

        query_embedding = embedding_model.encode(
            [query]
        )

        query_lower = query.strip().lower()

        summarize_triggers = [
            "summarize", "summary", "summarise",
            "overview", "brief", "explain the pdf",
            "what is this about", "what does this pdf",
            "entire", "whole", "full"
        ]

        is_broad_query = any(
            trigger in query_lower
            for trigger in summarize_triggers
        )

        if is_broad_query:

            context = "\n\n".join(stored_chunks)

            logger.info(
                f"Broad query detected, using all {len(stored_chunks)} chunks"
            )

        else:

            distances, indices = faiss_index.search(
                query_embedding,
                6
            )

            context = ""

            for idx in indices[0]:
                context += stored_chunks[idx]
                context += "\n\n"

            logger.info(
                f"Specific query, using top 6 chunks"
            )

        prompt = f"""
Answer ONLY using the context below.

Context:
{context}

Question:
{query}
"""

        response = model.generate_content(
            prompt
        )

        redis_client.setex(
            query,
            CACHE_EXPIRY,
            response.text
        )

        save_rag_history(
            user_email,
            query,
            response.text
        )

        return {
            "success": True,
            "data": {
                "question": query,
                "answer": response.text,
                "source": "gemini"
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"RAG Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )