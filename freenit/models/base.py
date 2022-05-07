import ormar
from passlib.hash import pbkdf2_sha256

from ..config import getConfig


def encrypt(password: str) -> str:
    config = getConfig()
    return pbkdf2_sha256.hash(f"{config.secret}{password}")


class BaseModel(ormar.Model):
    async def patch(self, fields):
        result = {}
        data = fields.dict()
        for k in data:
            if data[k] is not None:
                result[k] = data[k]
        return await self.update(**result)


class UserMixin(BaseModel):
    def __init__(self, email: str = "", password: str = "") -> None:
        self.email = email
        self.password = password

    def __setattr__(self, name: str, value) -> None:
        if name == "password":
            self.__dict__[name] = encrypt(value)
        else:
            self.__dict__[name] = value

    def check(self, password: str) -> bool:
        return encrypt(password) == self.password

    @classmethod
    def get(cls, email: str):
        return cls(email)

    @classmethod
    async def login(cls, email: str, password: str):
        user = cls.get(email)
        if user.check(password):
            return user
        return None
