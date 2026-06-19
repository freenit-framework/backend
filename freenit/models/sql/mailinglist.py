from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import oxyde
import pydantic

from freenit.models.sql.base import OxydeBaseModel

NotFoundError = oxyde.NotFoundError
IntegrityError = oxyde.IntegrityError


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


MailingList.model_rebuild()
PendingSubscriber.model_rebuild()
ModerationMessage.model_rebuild()
