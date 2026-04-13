from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr

from .base import User


class UserOptional(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = None
    password: str | None = None
    fullname: str | None = None
    active: bool | None = None
    admin: bool | None = None

