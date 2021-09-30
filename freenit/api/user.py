from ..auth import cookieAuthentication
from ..config import getConfig
from .router import api

config = getConfig()
auth = config.get_user()

tags = ["auth"]
api.include_router(
    auth.fastapiUsers.get_auth_router(cookieAuthentication),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    auth.fastapiUsers.get_register_router(),
    prefix="/auth",
    tags=tags
)
api.include_router(
    auth.fastapiUsers.get_reset_password_router(),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    auth.fastapiUsers.get_verify_router(),
    prefix="/auth",
    tags=tags,
)
api.include_router(
    auth.fastapiUsers.get_users_router(),
    prefix="/users",
    tags=["users"]
)
