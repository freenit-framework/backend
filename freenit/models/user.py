from typing import Optional

import databases
import sqlalchemy
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, models
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import OrmarBaseUserModel, OrmarUserDatabase

from ..auth import authBackends
from .mixins import MainMeta

SECRET = "SECRET"
DATABASE_URL = "sqlite:///test.db"
metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL)
engine = sqlalchemy.create_engine(DATABASE_URL)


class UserModel(OrmarBaseUserModel):
    class Meta:
        tablename = "users"
        metadata = metadata
        database = database


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
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

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
    [authBackends],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

current_active_user = fastapiUsers.current_user(active=True)
