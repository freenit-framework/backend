from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, models
from fastapi_users.db import OrmarBaseUserModel, OrmarUserDatabase

from ..config import getConfig
from ..auth import authBackends

config = getConfig()


class UserModel(OrmarBaseUserModel):
    class Meta:
        tablename = "users"
        metadata = config.metadata
        database = config.database


class User(models.BaseUser):
    pass


class UserCreate(models.BaseUserCreate):
    pass


class UserUpdate(User, models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB):
    pass


class UserManager(BaseUserManager[UserCreate, UserDB]):
    user_db_model = UserDB
    reset_password_token_secret = config.secret
    verification_token_secret = config.secret

    async def on_after_register(
        self,
        user: UserDB,
        request: Optional[Request] = None
    ):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self,
        user: UserDB,
        token: str,
        request: Optional[Request] = None
    ):
        print(
            f"User {user.id} has forgot their password. Reset token: {token}"
        )

    async def after_verification_request(
        self,
        user: UserDB,
        token: str,
        request: Optional[Request] = None
    ):
        print(
            f"Verification requested for user {user.id}. Verification token: {token}"
        )


def get_user_db():
    yield OrmarUserDatabase(UserDB, UserModel)


def get_user_manager(user_db: OrmarUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


fastapiUsers = FastAPIUsers(
    get_user_manager,
    authBackends,
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

current_active_user = fastapiUsers.current_user(active=True)
