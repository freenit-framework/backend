import ormar
from passlib.hash import pbkdf2_sha256

from ..config import getConfig


class BaseModel(ormar.Model):
    async def patch(self, fields):
        result = {}
        data = fields.dict()
        for k in data:
            if data[k] is not None:
                result[k] = data[k]
        return await self.update(**result)


class UserMixin:
    def __init__(
        self, email: str = "", password: str = "", active: bool = False
    ) -> None:
        self.email = email
        self.password = password
        self.active = active

    def __setattr__(self, name: str, value) -> None:
        if name == "password":
            config = getConfig()
            self.__dict__[name] = pbkdf2_sha256.hash(f"{config.secret}{value}")
        else:
            self.__dict__[name] = value

    def check(self, password: str) -> bool:
        config = getConfig()
        return pbkdf2_sha256.verify(f"{config.secret}{password}", self.password)
