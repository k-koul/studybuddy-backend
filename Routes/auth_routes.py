from fastapi import APIRouter

from Models.user_model import User

from Services.auth_services import (
    register_user,
    login_user
)

router = APIRouter()

# ---------------- REGISTER ROUTE ----------------

@router.post("/register")
def register(user: User):

    return register_user(user)

# ---------------- LOGIN ROUTE ----------------

@router.post("/login")
def login(user: User):

    return login_user(user)

