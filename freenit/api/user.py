from fastapi import Request
from ..models.user import fastapiUsers, UserDB
from ..auth import cookieAuthentication
from .router import api

tags = ["auth"]
api.include_router(
    fastapiUsers.get_auth_router(cookieAuthentication),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    fastapiUsers.get_register_router(on_after_register),
    prefix="/auth",
    tags=tags
)
api.include_router(
    fastapiUsers.get_reset_password_router(
        config.secret,
        after_forgot_password=on_after_forgot_password
    ),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    fastapiUsers.get_verify_router(
        config.secret,
        after_verification_request=after_verification_request
    ),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    fastapiUsers.get_users_router(),
    prefix="/users",
    tags=["users"]
)
