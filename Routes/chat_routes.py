from fastapi import APIRouter

from Services.chat_services import (
    chat_with_ai,
    create_session,
    get_sessions,
    get_messages,
    delete_session,
    rename_session
)

router = APIRouter()


@router.post("/chat/session")
def new_session(
    user_email: str,
    title: str
):

    return create_session(
        user_email,
        title
    )


@router.patch("/chat/session/rename")
def rename(
    session_id: int,
    user_email: str,
    new_title: str
):

    return rename_session(
        session_id,
        user_email,
        new_title
    )


@router.get("/chat/sessions")
def sessions(user_email: str):

    return get_sessions(
        user_email
    )


@router.get("/chat/messages")
def messages(session_id: int):

    return get_messages(
        session_id
    )


@router.delete("/chat/session")
def remove_session(
    session_id: int,
    user_email: str
):

    return delete_session(
        session_id,
        user_email
    )


@router.post("/chat")
def chat(
    message: str,
    user_email: str,
    session_id: int,
    is_first: bool = False
):

    return chat_with_ai(
        message,
        user_email,
        session_id,
        is_first
    )