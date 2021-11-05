from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import CookieAuthentication
from fastapi_users.db import OrmarUserDatabase

from .config import getConfig

config = getConfig()
auth = config.get_user()
cookieAuthentication = CookieAuthentication(
    secret=config.secret,
    lifetime_seconds=3600,
    cookie_secure=config.cookie_secure,
)
authBackends = [cookieAuthentication]


class UserManager(BaseUserManager[auth.UserCreate, auth.UserDB]):
    user_db_model = auth.UserDB
    reset_password_token_secret = config.secret
    verification_token_secret = config.secret

    async def on_after_register(
        self, user: auth.UserDB, request: Optional[Request] = None
    ):
        pass

    async def on_after_forgot_password(
        self, user: auth.UserDB, token: str, request: Optional[Request] = None
    ):
        pass

    async def after_verification_request(
        self, user: auth.UserDB, token: str, request: Optional[Request] = None
    ):
        pass


def get_user_db():
    yield OrmarUserDatabase(auth.UserDB, auth.UserModel)


def get_user_manager(user_db: OrmarUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


fastapiUsers = FastAPIUsers(
    get_user_manager,
    authBackends,
    auth.User,
    auth.UserCreate,
    auth.UserUpdate,
    auth.UserDB,
)

current_user = fastapiUsers.current_user()
current_active_user = fastapiUsers.current_user(active=True)
current_active_verified_user = fastapiUsers.current_user(active=True, verified=True)
current_superuser = fastapiUsers.current_user(active=True, superuser=True)
