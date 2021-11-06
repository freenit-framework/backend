from fastapi import Depends
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


class CurrentUser:
    def __init__(self) -> None:
        self.user = fastapiUsers.current_user()
        self.active = fastapiUsers.current_user(active=True)
        self.verified = fastapiUsers.current_user(verified=True)
        self.active_verified = fastapiUsers.current_user(active=True, verified=True)
        self.superuser = fastapiUsers.current_user(active=True, superuser=True)


current_user = CurrentUser()
