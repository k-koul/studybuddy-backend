from fastapi import APIRouter, UploadFile

from Services.rag_services import (
    process_pdf,
    ask_question,
    get_rag_history,
    delete_rag_history
)

router = APIRouter()


@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile):

    return await process_pdf(file)


@router.post("/ask")
def ask(
    query: str,
    user_email: str
):

    return ask_question(query, user_email)


@router.get("/rag/history")
def rag_history(user_email: str):

    return get_rag_history(user_email)


@router.delete("/rag/history")
def remove_rag_history(
    entry_id: int,
    user_email: str
):

    return delete_rag_history(entry_id, user_email)