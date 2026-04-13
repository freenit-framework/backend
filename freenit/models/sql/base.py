from __future__ import annotations

from typing import ClassVar

import oxyde
import pydantic
from fastapi import HTTPException

from freenit.auth import verify
from freenit.config import getConfig

config = getConfig()


class OxydeBaseModel(oxyde.Model):
    @classmethod
    def dbtype(cls):
        return "sql"

    @property
    def pk(self):
        return self.id

    async def patch(self, fields):
        data = fields.model_dump(exclude_none=True)
        for key, value in data.items():
            setattr(self, key, value)
        await self.save(update_fields=data.keys())
        return self

    async def load_all(self):
        if hasattr(self, "roles"):
            object.__setattr__(self, "roles", await self.fetch_roles())
        if hasattr(self, "users"):
            object.__setattr__(self, "users", await self.fetch_users())
        return self


class RoleRelationManager:
    def __init__(self, user: User):
        self.user = user

    async def add(self, role: Role):
        try:
            await UserRole.objects.create(
                user=self.user,
                role=role,
                user_id=self.user.id,
                role_id=role.id,
            )
        except oxyde.IntegrityError:
            raise HTTPException(status_code=409, detail="User already assigned")
        object.__setattr__(self.user, "roles", await self.user.fetch_roles())

    async def remove(self, role: Role):
        link = await UserRole.objects.get(user_id=self.user.id, role_id=role.id)
        await link.delete()
        object.__setattr__(self.user, "roles", await self.user.fetch_roles())


class RoleList(list):
    def __init__(self, user: "User", roles: list["BaseRole"] | None = None):
        super().__init__(roles or [])
        self.user = user

    async def add(self, role: "BaseRole"):
        await RoleRelationManager(self.user).add(role)
        self[:] = await self.user.fetch_roles()

    async def remove(self, role: "BaseRole"):
        await RoleRelationManager(self.user).remove(role)
        self[:] = await self.user.fetch_roles()


class BaseRole(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    name: str = oxyde.Field(db_unique=True, db_index=True)
    users: list["User"] = oxyde.Field(default_factory=list, db_m2m=True, db_through="UserRole")

    class Meta:
        is_table = True
        table_name = "role"

    def model_post_init(self, __context):
        object.__setattr__(self, "users", list(getattr(self, "users", []) or []))

    async def fetch_users(self) -> list["User"]:
        users = await User.objects.prefetch("roles").all()
        return [user.email for user in users if any(role.id == self.id for role in user.roles)]


class User(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    email: pydantic.EmailStr = oxyde.Field(db_unique=True)
    password: str = oxyde.Field()
    fullname: str | None = oxyde.Field(default=None)
    active: bool = oxyde.Field(default=False)
    admin: bool = oxyde.Field(default=False)
    roles: list[BaseRole] = oxyde.Field(default_factory=list, db_m2m=True, db_through="UserRole")

    class Meta:
        is_table = True
        table_name = "user"

    def model_post_init(self, __context):
        object.__setattr__(self, "roles", RoleList(self, list(getattr(self, "roles", []) or [])))

    def check(self, password: str) -> bool:
        if self.password is None:
            return False
        return verify(password, self.password)

    @classmethod
    async def login(cls, credentials) -> "User":
        try:
            user = await cls.objects.prefetch("roles").filter(
                email=credentials.email, active=True
            ).get()
        except oxyde.NotFoundError:
            raise HTTPException(status_code=403, detail="Failed to login")
        if user.check(credentials.password):
            return user
        raise HTTPException(status_code=403, detail="Failed to login")

    async def fetch_roles(self) -> list[BaseRole]:
        links = await UserRole.objects.filter(user_id=self.id).all()
        role_ids = [link.role_id for link in links]
        if not role_ids:
            return RoleList(self, [])
        roles = await BaseRole.objects.filter(id__in=role_ids).all()
        return RoleList(self, roles)


class UserRole(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    user: User | None = oxyde.Field(default=None, db_fk="id", db_on_delete="CASCADE")
    role: BaseRole | None = oxyde.Field(default=None, db_fk="id", db_on_delete="CASCADE")

    class Meta:
        is_table = True
        table_name = "user_role"
        unique_together = [("user_id", "role_id")]


class Theme(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    name: str = oxyde.Field(db_unique=True)
    bg_color: str = oxyde.Field()
    bg_secondary_color: str = oxyde.Field()
    color_primary: str = oxyde.Field()
    color_lightGrey: str = oxyde.Field()
    color_grey: str = oxyde.Field()
    color_darkGrey: str = oxyde.Field()
    color_error: str = oxyde.Field()
    color_success: str = oxyde.Field()
    grid_maxWidth: str = oxyde.Field()
    grid_gutter: str = oxyde.Field()
    font_size: str = oxyde.Field()
    font_color: str = oxyde.Field()
    font_family_sans: str = oxyde.Field()
    font_family_mono: str = oxyde.Field()

    class Meta:
        is_table = True
        table_name = "theme"


User.model_rebuild()
BaseRole.model_rebuild()
UserRole.model_rebuild()
