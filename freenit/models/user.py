from fastapi_users import FastAPIUsers, models
from fastapi_users.db import OrmarBaseUserModel, OrmarUserDatabase
from ..auth import authBackends
from .mixins import MainMeta


class User(models.BaseUser):
    pass


class UserCreate(models.BaseUserCreate):
    pass


class UserUpdate(User, models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB):
    pass


class UserModel(OrmarBaseUserModel):
    class Meta(MainMeta):
        tablename = "users"


userDb = OrmarUserDatabase(UserDB, UserModel)
fastapiUsers = FastAPIUsers(userDb, authBackends, User, UserCreate, UserUpdate, UserDB)
