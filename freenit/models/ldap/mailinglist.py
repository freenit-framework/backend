from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from freenit.models.ldap.base import LDAPBaseModel


class NotFoundError(Exception):
    pass


class IntegrityError(Exception):
    pass


def _first(entry, attr, default=None):
    value = entry.get(attr)
    if not value:
        return default
    if isinstance(value, (list, tuple)):
        value = value[0]
    return value


def _int(entry, attr, default=None):
    value = _first(entry, attr)
    if value is None:
        return default
    return int(value)


def _bool(entry, attr, default=False):
    value = _first(entry, attr)
    if value is None:
        return default
    return str(value).upper() == "TRUE"


def _datetime(entry, attr, default=None):
    value = _first(entry, attr)
    if value is None:
        return default
    value = str(value)
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


class MailingList(LDAPBaseModel):
    id: int = Field(0, description="Numeric mailing list ID")
    name: str = Field("", description="Mailing list name")
    address: EmailStr = Field("", description="Primary list address")
    distribution_address: EmailStr = Field("", description="Distribution list address")
    archive_address: EmailStr = Field("", description="Archive account address")
    description: str | None = Field(None, description="Optional description")
    public: bool = Field(True, description="Publicly visible")
    archive_enabled: bool = Field(True, description="Archive enabled")
    moderation_enabled: bool = Field(False, description="Moderation enabled")
    principal_id: int | None = Field(None, description="Stalwart list principal ID")
    inbox_principal_id: int | None = Field(None, description="Stalwart inbox principal ID")
    archive_principal_id: int | None = Field(None, description="Stalwart archive principal ID")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    @classmethod
    def from_entry(cls, entry):
        return cls(
            dn=str(entry["dn"]),
            id=_int(entry, "mlidNumber", 0),
            name=_first(entry, "cn", ""),
            address=_first(entry, "mailinglistAddress", ""),
            distribution_address=_first(entry, "mailinglistDistributionAddress", ""),
            archive_address=_first(entry, "mailinglistArchiveAddress", ""),
            description=_first(entry, "description"),
            public=_bool(entry, "mailinglistPublic", True),
            archive_enabled=_bool(entry, "mailinglistArchiveEnabled", True),
            moderation_enabled=_bool(entry, "mailinglistModerationEnabled", False),
            principal_id=_int(entry, "principalId"),
            inbox_principal_id=_int(entry, "inboxPrincipalId"),
            archive_principal_id=_int(entry, "archivePrincipalId"),
            created_at=_datetime(entry, "createdAt"),
            updated_at=_datetime(entry, "updatedAt"),
        )


class PendingSubscriber(LDAPBaseModel):
    id: int = Field(0, description="Numeric pending subscriber ID")
    mailing_list_id: int = Field(0, description="Parent mailing list ID")
    email: EmailStr = Field("", description="Subscriber email")
    token: str = Field("", description="Confirmation token")
    action: str = Field("subscribe", description="subscribe or unsubscribe")
    created_at: datetime | None = Field(None, description="Creation timestamp")

    @classmethod
    def from_entry(cls, entry, mailing_list_id: int = 0):
        return cls(
            dn=str(entry["dn"]),
            id=_int(entry, "mlidNumber", 0),
            mailing_list_id=mailing_list_id,
            email=_first(entry, "mail", ""),
            token=_first(entry, "mailinglistToken", ""),
            action=_first(entry, "mailinglistAction", "subscribe"),
            created_at=_datetime(entry, "createdAt"),
        )


class ModerationMessage(LDAPBaseModel):
    id: int = Field(0, description="Numeric moderation message ID")
    mailing_list_id: int = Field(0, description="Parent mailing list ID")
    message_id: str | None = Field(None, description="Original Message-ID header")
    subject: str | None = Field(None, description="Message subject")
    sender: EmailStr | None = Field(None, description="Message sender")
    sent_at: datetime | None = Field(None, description="Original sent timestamp")
    text_body: str | None = Field(None, description="Plain text body")
    html_body: str | None = Field(None, description="HTML body")
    status: str = Field("pending", description="pending/approved/rejected")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    decided_at: datetime | None = Field(None, description="Decision timestamp")

    @classmethod
    def from_entry(cls, entry, mailing_list_id: int = 0):
        return cls(
            dn=str(entry["dn"]),
            id=_int(entry, "mlidNumber", 0),
            mailing_list_id=mailing_list_id,
            message_id=_first(entry, "mailinglistMessageId"),
            subject=_first(entry, "mailinglistSubject"),
            sender=_first(entry, "mailinglistSender"),
            sent_at=_datetime(entry, "sentAt"),
            text_body=_first(entry, "textBody"),
            html_body=_first(entry, "htmlBody"),
            status=_first(entry, "mailinglistStatus", "pending"),
            created_at=_datetime(entry, "createdAt"),
            decided_at=_datetime(entry, "decidedAt"),
        )


class MailingListCreate(BaseModel):
    name: str
    domain: str
    description: str | None = None
    public: bool = True
    archive_enabled: bool = True
    moderation_enabled: bool = False


class MailingListUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    public: bool | None = None
    archive_enabled: bool | None = None
    moderation_enabled: bool | None = None
