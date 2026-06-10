from fastapi import (
    FastAPI,
    HTTPException,
    Request
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from fastapi.responses import (
    JSONResponse
)

from Routes import auth_routes
from Routes import rag_routes
from Routes import chat_routes

from config import FRONTEND_URL

from database import init_db

app = FastAPI()

@app.exception_handler(
    HTTPException
)
async def http_exception_handler(
    request: Request,
    exc: HTTPException
):

    return JSONResponse(

        status_code=exc.status_code,

        content={
            "success": False,
            "error": exc.detail
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):

    return JSONResponse(

        status_code=500,

        content={
            "success": False,
            "error": str(exc)
        }
    )


init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://studybuddy-frontend-blush.vercel.app",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():

    return {
        "message":
        "Backend Running"
    }


app.include_router(
    auth_routes.router
)

app.include_router(
    rag_routes.router
)

app.include_router(
    chat_routes.router
)