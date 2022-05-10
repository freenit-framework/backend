import ormar
import pydantic

from ..auth import verify
from ..config import getConfig
from .metaclass import AllOptional

config = getConfig()


class OrmarBaseModel(ormar.Model):
    async def patch(self, fields):
        result = {}
        data = fields.dict()
        for k in data:
            if data[k] is not None:
                result[k] = data[k]
        return await self.update(**result)


class OrmarUserMixin:
    id: int = ormar.Integer(primary_key=True)
    email: pydantic.EmailStr = ormar.Text(unique=True)
    password: str = ormar.Text()
    active: bool = ormar.Boolean(default=False)


class User(OrmarBaseModel, OrmarUserMixin):
    class Meta(config.meta):
        tablename = "users"

    def check(self, password: str) -> bool:
        return verify(password, self.password)


class UserOptional(User, metaclass=AllOptional):
    pass
