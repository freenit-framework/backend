from ..models.user import fastapiUsers
from ..auth import cookieAuthentication
from ..config import getConfig
from .router import api

config = getConfig()

tags = ["auth"]
api.include_router(
    fastapiUsers.get_auth_router(cookieAuthentication),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    fastapiUsers.get_register_router(),
    prefix="/auth",
    tags=tags
)
api.include_router(
    fastapiUsers.get_reset_password_router(),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    fastapiUsers.get_verify_router(),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    fastapiUsers.get_users_router(),
    prefix="/users",
    tags=["users"]
)
