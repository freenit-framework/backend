from __future__ import annotations

from datetime import datetime
from typing import ClassVar
from uuid import uuid4

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
    omemo_bundle: str | None = oxyde.Field(default=None)
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


class MailingList(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    name: str = oxyde.Field(db_unique=True)
    address: pydantic.EmailStr = oxyde.Field(db_unique=True)
    distribution_address: pydantic.EmailStr = oxyde.Field(db_unique=True)
    archive_address: pydantic.EmailStr = oxyde.Field(db_unique=True)
    description: str | None = oxyde.Field(default=None)
    public: bool = oxyde.Field(default=True)
    archive_enabled: bool = oxyde.Field(default=True)
    moderation_enabled: bool = oxyde.Field(default=False)
    principal_id: int | None = oxyde.Field(default=None)
    inbox_principal_id: int | None = oxyde.Field(default=None)
    archive_principal_id: int | None = oxyde.Field(default=None)
    created_at: datetime | None = oxyde.Field(default=None)
    updated_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "mailing_list"


class PendingSubscriber(OxydeBaseModel):
    """Subscriptions/unsubscriptions awaiting email confirmation."""

    id: int | None = oxyde.Field(default=None, db_pk=True)
    mailing_list: MailingList | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    email: pydantic.EmailStr = oxyde.Field()
    token: str = oxyde.Field(default_factory=lambda: str(uuid4()))
    action: str = oxyde.Field(default="subscribe")
    created_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "pending_subscriber"
        unique_together = [("mailing_list_id", "email", "action")]


class ModerationMessage(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    mailing_list: MailingList | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    message_id: str | None = oxyde.Field(default=None)
    subject: str | None = oxyde.Field(default=None)
    sender: pydantic.EmailStr | None = oxyde.Field(default=None)
    sent_at: datetime | None = oxyde.Field(default=None)
    text_body: str | None = oxyde.Field(default=None)
    html_body: str | None = oxyde.Field(default=None)
    status: str = oxyde.Field(default="pending")
    created_at: datetime | None = oxyde.Field(default=None)
    decided_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "moderation_message"


User.model_rebuild()
BaseRole.model_rebuild()
UserRole.model_rebuild()
MailingList.model_rebuild()
PendingSubscriber.model_rebuild()
ModerationMessage.model_rebuild()
