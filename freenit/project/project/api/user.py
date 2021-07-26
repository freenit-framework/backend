from fastapi import Request

from freenit.auth import cookieAuthentication
from freenit.config import getConfig

from ..models.user import UserDB, fastapiUsers
from .router import api

config = getConfig()


def on_after_register(user: UserDB, request: Request):
    print(f"User {user.id} has registered.")


def on_after_forgot_password(user: UserDB, token: str, request: Request):
    print(f"User {user.id} has forgot their password. Reset token: {token}")


def after_verification_request(user: UserDB, token: str, request: Request):
    print(f"Verification requested for user {user.id}. Verification token: {token}")


tags = ["auth"]
api.include_router(
    fastapiUsers.get_auth_router(cookieAuthentication),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    fastapiUsers.get_register_router(on_after_register), prefix="/auth", tags=tags
)
api.include_router(
    fastapiUsers.get_reset_password_router(
        config.secret, after_forgot_password=on_after_forgot_password
    ),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    fastapiUsers.get_verify_router(
        config.secret, after_verification_request=after_verification_request
    ),
    prefix="/auth",
    tags=tags,
)
api.include_router(fastapiUsers.get_users_router(), prefix="/users", tags=["users"])
