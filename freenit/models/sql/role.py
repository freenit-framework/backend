from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .base import BaseRole as Role


class RoleOptional(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None

