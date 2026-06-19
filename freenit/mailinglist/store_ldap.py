from __future__ import annotations

from datetime import datetime, timezone
from math import ceil

from bonsai import LDAPEntry, LDAPSearchScope, errors
from fastapi import HTTPException

from freenit.config import getConfig
from freenit.models.ldap.base import class2filter, get_client, next_mlid, save_data
from freenit.models.mailinglist import MailingList, ModerationMessage, PendingSubscriber
from freenit.models.pagination import Page

config = getConfig()


def _ldap_dt(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y%m%d%H%M%SZ")


def _ldap_bool(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def _list_dn(name: str) -> str:
    return config.ldap.mailinglistDN.format(name)


def _pending_dn(list_name: str, token: str) -> str:
    return f"cn={token},{_list_dn(list_name)}"


def _moderation_dn(list_name: str, msg_id: int) -> str:
    return f"cn={msg_id},{_list_dn(list_name)}"


def _ml_filter():
    return class2filter(config.ldap.mailinglistClasses)


def _pending_filter():
    return class2filter(config.ldap.pendingSubscriberClasses)


def _moderation_filter():
    return class2filter(config.ldap.moderationMessageClasses)


async def _search_list_by_id(list_id: int):
    classes = _ml_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.mailinglistBase,
            LDAPSearchScope.SUB,
            f"(&{classes}(mlidNumber={list_id}))",
        )
    if len(res) < 1:
        raise HTTPException(status_code=404, detail="No such mailing list")
    if len(res) > 1:
        raise HTTPException(status_code=409, detail="Multiple mailing lists found")
    return res[0]


async def _search_list_by_name(name: str):
    classes = _ml_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.mailinglistBase,
            LDAPSearchScope.SUB,
            f"(&{classes}(cn={name}))",
        )
    return res[0] if res else None


async def _count_by_addresses(addresses: list[str]) -> int:
    classes = _ml_filter()
    address_filters = ""
    for addr in addresses:
        address_filters += (
            f"(mailinglistAddress={addr})"
            f"(mailinglistDistributionAddress={addr})"
            f"(mailinglistArchiveAddress={addr})"
        )
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.mailinglistBase,
            LDAPSearchScope.SUB,
            f"(&{classes}(|{address_filters}))",
        )
    return len(res)


async def get_mailing_list(id: int) -> MailingList:
    entry = await _search_list_by_id(id)
    return MailingList.from_entry(entry)


async def list_mailing_lists(
    page: int,
    perpage: int,
    public: bool | None = None,
) -> Page[MailingList]:
    classes = _ml_filter()
    filter_exp = classes
    if public is not None:
        filter_exp = f"(&{classes}(mailinglistPublic={_ldap_bool(public)}))"
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.mailinglistBase,
            LDAPSearchScope.SUB,
            filter_exp,
        )
    data = [MailingList.from_entry(entry) for entry in res]
    data.sort(key=lambda ml: ml.id, reverse=True)
    total = len(data)
    pages = ceil(total / perpage) if perpage else 1
    if total > 0 and page > pages:
        raise HTTPException(status_code=404, detail="No such page")
    offset = max(page - 1, 0) * perpage
    page_data = data[offset : offset + perpage]
    return Page(total=total, page=page, pages=pages, perpage=perpage, data=page_data)


async def count_mailing_lists_by_addresses(addresses: list[str]) -> int:
    return await _count_by_addresses(addresses)


async def create_mailing_list(**kwargs) -> MailingList:
    name = kwargs["name"]
    address = kwargs["address"]
    distribution_address = kwargs["distribution_address"]
    archive_address = kwargs["archive_address"]

    existing = await _search_list_by_name(name)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Mailing list already exists")

    if await _count_by_addresses([address, distribution_address, archive_address]) > 0:
        raise HTTPException(
            status_code=409, detail="Mailing list address already in use"
        )

    list_id = await next_mlid()
    now = kwargs.get("created_at") or datetime.utcnow()
    dn = _list_dn(name)
    entry = LDAPEntry(dn)
    entry["objectClass"] = config.ldap.mailinglistClasses
    entry["cn"] = name
    entry["mlidNumber"] = list_id
    entry["mailinglistAddress"] = address
    entry["mailinglistDistributionAddress"] = distribution_address
    entry["mailinglistArchiveAddress"] = archive_address
    description = kwargs.get("description")
    if description:
        entry["description"] = description
    entry["mailinglistPublic"] = _ldap_bool(kwargs.get("public", True))
    entry["mailinglistArchiveEnabled"] = _ldap_bool(kwargs.get("archive_enabled", True))
    entry["mailinglistModerationEnabled"] = _ldap_bool(
        kwargs.get("moderation_enabled", False)
    )
    for key, attr in [
        ("principal_id", "principalId"),
        ("inbox_principal_id", "inboxPrincipalId"),
        ("archive_principal_id", "archivePrincipalId"),
    ]:
        value = kwargs.get(key)
        if value is not None:
            entry[attr] = int(value)
    entry["createdAt"] = _ldap_dt(now)
    entry["updatedAt"] = _ldap_dt(now)

    try:
        await save_data(entry)
    except errors.AlreadyExists:
        raise HTTPException(status_code=409, detail="Mailing list already exists")

    return MailingList(
        dn=dn,
        id=list_id,
        name=name,
        address=address,
        distribution_address=distribution_address,
        archive_address=archive_address,
        description=description,
        public=kwargs.get("public", True),
        archive_enabled=kwargs.get("archive_enabled", True),
        moderation_enabled=kwargs.get("moderation_enabled", False),
        principal_id=kwargs.get("principal_id"),
        inbox_principal_id=kwargs.get("inbox_principal_id"),
        archive_principal_id=kwargs.get("archive_principal_id"),
        created_at=now,
        updated_at=now,
    )


async def update_mailing_list(mailing_list: MailingList, data) -> MailingList:
    fields = data.model_dump(exclude_none=True)
    if not fields:
        return mailing_list

    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(mailing_list.dn, LDAPSearchScope.BASE)
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such mailing list")
        entry = res[0]

        if "description" in fields:
            entry["description"] = fields["description"] or []
        if "public" in fields:
            entry["mailinglistPublic"] = _ldap_bool(fields["public"])
        if "archive_enabled" in fields:
            entry["mailinglistArchiveEnabled"] = _ldap_bool(fields["archive_enabled"])
        if "moderation_enabled" in fields:
            entry["mailinglistModerationEnabled"] = _ldap_bool(
                fields["moderation_enabled"]
            )
        entry["updatedAt"] = _ldap_dt(datetime.utcnow())
        await entry.modify()

    for key, value in fields.items():
        setattr(mailing_list, key, value)
    mailing_list.updated_at = datetime.utcnow()
    return mailing_list


async def delete_mailing_list(mailing_list: MailingList) -> None:
    client = get_client()
    async with client.connect(is_async=True) as conn:
        children = await conn.search(
            mailing_list.dn,
            LDAPSearchScope.SUB,
            "(objectClass=*)",
            attrlist=["objectClass"],
        )
        for child in children:
            child_dn = str(child["dn"])
            if child_dn != mailing_list.dn:
                await child.delete()
        res = await conn.search(mailing_list.dn, LDAPSearchScope.BASE)
        if res:
            await res[0].delete()


async def get_pending_subscriber(
    mailing_list_id: int,
    token: str,
    action: str,
) -> PendingSubscriber:
    list_entry = await _search_list_by_id(mailing_list_id)
    list_name = str(list_entry["cn"][0])
    classes = _pending_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _list_dn(list_name),
            LDAPSearchScope.ONELEVEL,
            f"(&{classes}(mailinglistToken={token})(mailinglistAction={action}))",
        )
    if len(res) < 1:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    return PendingSubscriber.from_entry(res[0], mailing_list_id)


async def get_pending_subscriber_by_email(
    mailing_list_id: int,
    email: str,
    action: str,
) -> PendingSubscriber:
    list_entry = await _search_list_by_id(mailing_list_id)
    list_name = str(list_entry["cn"][0])
    classes = _pending_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _list_dn(list_name),
            LDAPSearchScope.ONELEVEL,
            f"(&{classes}(mail={email})(mailinglistAction={action}))",
        )
    if len(res) < 1:
        raise HTTPException(status_code=404, detail="Pending subscriber not found")
    return PendingSubscriber.from_entry(res[0], mailing_list_id)


async def create_pending_subscriber(
    mailing_list: MailingList,
    email: str,
    action: str,
    token: str,
) -> PendingSubscriber:
    pending_id = await next_mlid()
    created_at = datetime.utcnow()
    dn = _pending_dn(mailing_list.name, token)
    entry = LDAPEntry(dn)
    entry["objectClass"] = config.ldap.pendingSubscriberClasses
    entry["cn"] = token
    entry["mlidNumber"] = pending_id
    entry["mail"] = email
    entry["mailinglistToken"] = token
    entry["mailinglistAction"] = action
    entry["createdAt"] = _ldap_dt(created_at)
    await save_data(entry)
    return PendingSubscriber(
        dn=dn,
        id=pending_id,
        mailing_list_id=mailing_list.id,
        email=email,
        token=token,
        action=action,
        created_at=created_at,
    )


async def delete_pending_subscriber(pending: PendingSubscriber) -> None:
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(pending.dn, LDAPSearchScope.BASE)
        if res:
            await res[0].delete()


async def get_moderation_message(
    mailing_list_id: int,
    msg_id: int,
) -> ModerationMessage:
    list_entry = await _search_list_by_id(mailing_list_id)
    list_name = str(list_entry["cn"][0])
    classes = _moderation_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _list_dn(list_name),
            LDAPSearchScope.ONELEVEL,
            f"(&{classes}(mlidNumber={msg_id}))",
        )
    if len(res) < 1:
        raise HTTPException(status_code=404, detail="No such moderation message")
    return ModerationMessage.from_entry(res[0], mailing_list_id)


async def list_moderation_messages(
    mailing_list_id: int,
    status: str,
    page: int,
    perpage: int,
) -> Page[ModerationMessage]:
    list_entry = await _search_list_by_id(mailing_list_id)
    list_name = str(list_entry["cn"][0])
    classes = _moderation_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _list_dn(list_name),
            LDAPSearchScope.ONELEVEL,
            f"(&{classes}(mailinglistStatus={status}))",
        )
    data = [ModerationMessage.from_entry(entry, mailing_list_id) for entry in res]
    data.sort(key=lambda msg: msg.created_at or datetime.min, reverse=True)
    total = len(data)
    pages = ceil(total / perpage) if perpage else 1
    if total > 0 and page > pages:
        raise HTTPException(status_code=404, detail="No such page")
    offset = max(page - 1, 0) * perpage
    page_data = data[offset : offset + perpage]
    return Page(total=total, page=page, pages=pages, perpage=perpage, data=page_data)


async def create_moderation_message(
    mailing_list: MailingList,
    message_id: str | None,
    subject: str | None,
    sender: str | None,
    sent_at: datetime,
    text_body: str | None,
    html_body: str | None,
    status: str,
    created_at: datetime,
) -> ModerationMessage:
    msg_id = await next_mlid()
    dn = _moderation_dn(mailing_list.name, msg_id)
    entry = LDAPEntry(dn)
    entry["objectClass"] = config.ldap.moderationMessageClasses
    entry["cn"] = str(msg_id)
    entry["mlidNumber"] = msg_id
    if message_id:
        entry["mailinglistMessageId"] = message_id
    if subject:
        entry["mailinglistSubject"] = subject
    if sender:
        entry["mailinglistSender"] = sender
    entry["sentAt"] = _ldap_dt(sent_at)
    if text_body:
        entry["textBody"] = text_body
    if html_body:
        entry["htmlBody"] = html_body
    entry["mailinglistStatus"] = status
    entry["createdAt"] = _ldap_dt(created_at)
    await save_data(entry)
    return ModerationMessage(
        dn=dn,
        id=msg_id,
        mailing_list_id=mailing_list.id,
        message_id=message_id,
        subject=subject,
        sender=sender,
        sent_at=sent_at,
        text_body=text_body,
        html_body=html_body,
        status=status,
        created_at=created_at,
        decided_at=None,
    )


async def save_moderation_message(
    moderation_message: ModerationMessage,
    update_fields: list[str],
) -> None:
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(moderation_message.dn, LDAPSearchScope.BASE)
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such moderation message")
        entry = res[0]
        mapping = {
            "status": "mailinglistStatus",
            "decided_at": "decidedAt",
        }
        for field in update_fields:
            attr = mapping.get(field, field)
            value = getattr(moderation_message, field)
            if field == "decided_at":
                value = _ldap_dt(value)
            if value is None:
                if attr in entry:
                    del entry[attr]
            else:
                entry[attr] = value
        await entry.modify()
