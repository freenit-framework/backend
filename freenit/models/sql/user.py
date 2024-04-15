from __future__ import annotations

import ormar
import ormar.exceptions
from fastapi import HTTPException

from freenit.auth import verify
from freenit.models.sql.base import (
    OrmarBaseModel,
    OrmarUserMixin,
    generate_optional,
    ormar_config,
)
from freenit.models.role import Role


class BaseUser(OrmarBaseModel, OrmarUserMixin):
    def check(self, password: str) -> bool:
        return verify(password, self.password)

    @classmethod
    async def login(cls, credentials) -> BaseUser:
        try:
            user = await cls.objects.get(email=credentials.email, active=True)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=403, detail="Failed to login")
        if user.check(credentials.password):
            return user
        raise HTTPException(status_code=403, detail="Failed to login")


class User(BaseUser, OrmarUserMixin):
    ormar_config = ormar_config.copy()

    roles = ormar.ManyToMany(Role, unique=True)


UserOptional = generate_optional(User)
UserOptionalPydantic = User.get_pydantic(exclude={"admin", "active"})
