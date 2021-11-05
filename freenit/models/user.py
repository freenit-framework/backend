from fastapi_users import models
from fastapi_users.db import OrmarBaseUserModel

from ..config import getConfig

config = getConfig()


class UserModel(OrmarBaseUserModel):
    class Meta(config.meta):
        tablename = "users"


class User(models.BaseUser):
    pass


class UserCreate(models.BaseUserCreate):
    pass


class UserUpdate(User, models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB):
    pass
