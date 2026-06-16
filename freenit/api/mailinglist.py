import logging
from datetime import datetime
from typing import Any, List
from uuid import uuid4

import oxyde
import pydantic
from fastapi import Depends, Header, HTTPException, Request

from freenit.api.router import route
from freenit.config import getConfig
from freenit.decorators import description
from freenit.mailinglist.mail import (
    subscribe_confirmation,
    unsubscribe_confirmation,
)
from freenit.mailinglist.worker import (
    approve_message,
    process_mailing_list,
    reject_message,
)
from freenit.mail import sendmail
from freenit.models.pagination import Page, paginate
from freenit.models.sql.base import MailingList, ModerationMessage, PendingSubscriber
from freenit.models.user import User
from freenit.permissions import mailinglist_perms
from freenit.stalwart import (
    add_external_member,
    create_archive_account,
    create_inbox_account,
    create_list_principal,
    delete_principal,
    fetch_email_bodies,
    fetch_email_summaries,
    fetch_mailbox_messages,
    fetch_principal,
    remove_external_member,
)

config = getConfig()
log = logging.getLogger("mailinglist")

tags = ["mailinglist"]


def _current_user(user=Depends(mailinglist_perms)):
    return user


def _require_admin(cur_user: User) -> None:
    if not cur_user.admin:
        raise HTTPException(status_code=403, detail="Only admin users can perform this action")


def _parse_address(address: pydantic.EmailStr) -> tuple[str, str]:
    local, _, domain = address.partition("@")
    return local, domain


class MailingListCreate(pydantic.BaseModel):
    name: str
    address: pydantic.EmailStr
    description: str | None = None
    public: bool = True
    archive_enabled: bool = True
    moderation_enabled: bool = False


class MailingListUpdate(pydantic.BaseModel):
    name: str | None = None
    description: str | None = None
    public: bool | None = None
    archive_enabled: bool | None = None
    moderation_enabled: bool | None = None


class MailingListResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    name: str
    address: pydantic.EmailStr
    distribution_address: pydantic.EmailStr
    archive_address: pydantic.EmailStr
    description: str | None = None
    public: bool
    archive_enabled: bool
    moderation_enabled: bool
    created_at: datetime | None = None


class PublicMailingListResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    name: str
    address: pydantic.EmailStr
    description: str | None = None


class SubscriberAction(pydantic.BaseModel):
    email: pydantic.EmailStr


class ArchiveEmailResponse(pydantic.BaseModel):
    id: str
    message_id: str | None = None
    subject: str | None = None
    sender: pydantic.EmailStr | None = None
    sent_at: datetime | None = None
    text_body: str | None = None
    html_body: str | None = None


class ModerationMessageResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    message_id: str | None = None
    subject: str | None = None
    sender: pydantic.EmailStr | None = None
    sent_at: datetime | None = None
    text_body: str | None = None
    html_body: str | None = None
    status: str
    created_at: datetime | None = None
    decided_at: datetime | None = None


class SubscriberResponse(pydantic.BaseModel):
    email: pydantic.EmailStr


async def _get_list(id: int) -> MailingList:
    try:
        return await MailingList.objects.get(id=id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such mailing list")


async def _get_pending(id: int, token: str, action: str) -> PendingSubscriber:
    try:
        return await PendingSubscriber.objects.filter(
            mailing_list_id=id, token=token, action=action
        ).get()
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="Invalid or expired token")


async def _get_moderation(id: int, msg_id: int) -> ModerationMessage:
    try:
        return await ModerationMessage.objects.filter(
            id=msg_id, mailing_list_id=id
        ).get()
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such moderation message")


@route("/mailinglists", tags=tags)
class MailingListListAPI:
    @staticmethod
    @description("Get mailing lists")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        cur_user: User = Depends(mailinglist_perms),
    ) -> Page[MailingListResponse]:
        _require_admin(cur_user)
        return await paginate(MailingList.objects, page, perpage)

    @staticmethod
    @description("Create mailing list")
    async def post(
        data: MailingListCreate,
        cur_user: User = Depends(mailinglist_perms),
    ) -> MailingListResponse:
        _require_admin(cur_user)
        local, domain = _parse_address(data.address)
        distribution_address = f"{local}-members@{domain}"
        archive_address = f"{local}-archive@{domain}"

        existing_count = await MailingList.objects.filter(
            address__in=[data.address, distribution_address, archive_address]
        ).count()
        if existing_count > 0:
            raise HTTPException(status_code=409, detail="Mailing list address already in use")

        try:
            inbox_id = await create_inbox_account(data.name, data.address)
            list_id = await create_list_principal(data.name, distribution_address)
            archive_id = await create_archive_account(data.name, archive_address)
            await add_external_member(list_id, archive_address)
        except Exception as e:
            log.error("Failed to create Stalwart principals: %s", e)
            raise HTTPException(status_code=502, detail=f"Stalwart error: {e}")

        try:
            now = datetime.utcnow()
            mailing_list = await MailingList.objects.create(
                name=data.name,
                address=data.address,
                distribution_address=distribution_address,
                archive_address=archive_address,
                description=data.description,
                public=data.public,
                archive_enabled=data.archive_enabled,
                moderation_enabled=data.moderation_enabled,
                principal_id=list_id,
                inbox_principal_id=inbox_id,
                archive_principal_id=archive_id,
                created_at=now,
                updated_at=now,
            )
        except oxyde.IntegrityError as e:
            raise HTTPException(status_code=409, detail=f"Mailing list already exists: {e}")

        return MailingListResponse.model_validate(mailing_list)


@route("/mailinglists/public", tags=tags)
class MailingListPublicAPI:
    @staticmethod
    @description("Get public mailing lists")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
    ) -> Page[PublicMailingListResponse]:
        return await paginate(
            MailingList.objects.filter(public=True),
            page,
            perpage,
        )


@route("/mailinglists/{id}", tags=tags)
class MailingListDetailAPI:
    @staticmethod
    async def get(id: int, cur_user: User = Depends(mailinglist_perms)) -> MailingListResponse:
        _require_admin(cur_user)
        mailing_list = await _get_list(id)
        return MailingListResponse.model_validate(mailing_list)

    @staticmethod
    async def patch(
        id: int,
        data: MailingListUpdate,
        cur_user: User = Depends(mailinglist_perms),
    ) -> MailingListResponse:
        _require_admin(cur_user)
        mailing_list = await _get_list(id)
        await mailing_list.patch(data)
        return MailingListResponse.model_validate(mailing_list)

    @staticmethod
    async def delete(id: int, cur_user: User = Depends(mailinglist_perms)) -> MailingListResponse:
        _require_admin(cur_user)
        mailing_list = await _get_list(id)
        try:
            for principal_id in [
                mailing_list.inbox_principal_id,
                mailing_list.principal_id,
                mailing_list.archive_principal_id,
            ]:
                if principal_id:
                    await delete_principal(principal_id)
        except Exception as e:
            log.error("Failed to delete Stalwart principals for list %s: %s", id, e)
        await mailing_list.delete()
        return MailingListResponse.model_validate(mailing_list)


@route("/mailinglists/{id}/subscribers", tags=tags)
class MailingListSubscribersAPI:
    @staticmethod
    @description("Get confirmed subscribers from Stalwart")
    async def get(
        id: int,
        cur_user: User = Depends(mailinglist_perms),
    ) -> List[SubscriberResponse]:
        _require_admin(cur_user)
        mailing_list = await _get_list(id)
        if not mailing_list.principal_id:
            return []
        try:
            principal = await fetch_principal(mailing_list.principal_id)
        except Exception as e:
            log.error("Failed to fetch Stalwart principal %s: %s", mailing_list.principal_id, e)
            raise HTTPException(status_code=502, detail=f"Stalwart error: {e}")
        members = principal.get("externalMembers", [])
        return [SubscriberResponse(email=email) for email in members]


def _email_address(header_value: dict[str, Any] | list[dict[str, Any]] | None) -> str | None:
    if not header_value:
        return None
    if isinstance(header_value, list):
        header_value = header_value[0]
    return header_value.get("email") or header_value.get("address")


@route("/mailinglists/{id}/archive", tags=tags)
class MailingListArchiveAPI:
    @staticmethod
    @description("Get public archive")
    async def get(
        id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
    ) -> Page[ArchiveEmailResponse]:
        mailing_list = await _get_list(id)
        if not mailing_list.public or not mailing_list.archive_enabled:
            raise HTTPException(status_code=403, detail="Archive not available")
        try:
            email_ids = await fetch_mailbox_messages(mailing_list.archive_address, "inbox")
        except Exception as e:
            log.error("Failed to fetch archive mailbox for %s: %s", mailing_list.archive_address, e)
            raise HTTPException(status_code=502, detail=f"Stalwart error: {e}")

        total = len(email_ids)
        pages = (total + perpage - 1) // perpage
        offset = (page - 1) * perpage
        page_ids = email_ids[offset:offset + perpage]

        try:
            summaries = await fetch_email_summaries(mailing_list.archive_address, page_ids)
        except Exception as e:
            log.error("Failed to fetch archive summaries for %s: %s", mailing_list.archive_address, e)
            raise HTTPException(status_code=502, detail=f"Stalwart error: {e}")

        data = []
        for item in summaries:
            received_at = item.get("receivedAt")
            sent_at = datetime.fromisoformat(received_at.replace("Z", "+00:00")) if received_at else None
            message_ids = item.get("messageId", [])
            data.append(ArchiveEmailResponse(
                id=item.get("id"),
                message_id=message_ids[0] if isinstance(message_ids, list) and message_ids else None,
                subject=item.get("subject"),
                sender=_email_address(item.get("from")),
                sent_at=sent_at,
            ))

        return Page(data=data, page=page, perpage=perpage, pages=pages, total=total)


@route("/mailinglists/{id}/archive/{msg_id}", tags=tags)
class MailingListArchiveMessageAPI:
    @staticmethod
    @description("Get single archive message")
    async def get(id: int, msg_id: str) -> ArchiveEmailResponse:
        mailing_list = await _get_list(id)
        if not mailing_list.public or not mailing_list.archive_enabled:
            raise HTTPException(status_code=403, detail="Archive not available")
        try:
            email_data = await fetch_email_bodies(mailing_list.archive_address, msg_id)
        except Exception as e:
            log.error("Failed to fetch archive message %s for %s: %s", msg_id, mailing_list.archive_address, e)
            raise HTTPException(status_code=502, detail=f"Stalwart error: {e}")
        if not email_data:
            raise HTTPException(status_code=404, detail="No such message")

        received_at = email_data.get("receivedAt")
        sent_at = datetime.fromisoformat(received_at.replace("Z", "+00:00")) if received_at else None
        message_ids = email_data.get("messageId", [])

        body_values = email_data.get("bodyValues", {})
        text_body = None
        html_body = None
        for part in email_data.get("textBody", []):
            part_id = part.get("partId")
            if part_id and part_id in body_values:
                text_body = body_values[part_id].get("value")
                break
        for part in email_data.get("htmlBody", []):
            part_id = part.get("partId")
            if part_id and part_id in body_values:
                html_body = body_values[part_id].get("value")
                break

        return ArchiveEmailResponse(
            id=email_data.get("id"),
            message_id=message_ids[0] if isinstance(message_ids, list) and message_ids else None,
            subject=email_data.get("subject"),
            sender=_email_address(email_data.get("from")),
            sent_at=sent_at,
            text_body=text_body,
            html_body=html_body,
        )


@route("/mailinglists/{id}/subscribe", tags=tags)
class MailingListSubscribeAPI:
    @staticmethod
    @description("Request subscription")
    async def post(
        id: int,
        data: SubscriberAction,
        request: Request,
    ) -> dict[str, str]:
        mailing_list = await _get_list(id)
        if not mailing_list.public:
            raise HTTPException(status_code=403, detail="Subscribing is not allowed")

        try:
            pending = await PendingSubscriber.objects.filter(
                mailing_list_id=id, email=data.email, action="subscribe"
            ).get()
        except oxyde.NotFoundError:
            pending = await PendingSubscriber.objects.create(
                mailing_list=mailing_list,
                mailing_list_id=mailing_list.id,
                email=data.email,
                action="subscribe",
                token=str(uuid4()),
                created_at=datetime.utcnow(),
            )
        confirm_url = f"{request.base_url}api/v1/mailinglists/{id}/confirm/{pending.token}"
        msg = subscribe_confirmation(mailing_list.name, mailing_list.address, confirm_url)
        msg["To"] = data.email
        try:
            sendmail([data.email], msg)
        except Exception as e:
            log.error("Failed to send subscribe confirmation to %s: %s", data.email, e)
            raise HTTPException(status_code=502, detail="Failed to send confirmation email")
        return {"detail": "Please check your email to confirm subscription"}


@route("/mailinglists/{id}/confirm/{token}", tags=tags)
class MailingListConfirmAPI:
    @staticmethod
    @description("Confirm subscription")
    async def get(id: int, token: str) -> dict[str, str]:
        mailing_list = await _get_list(id)
        if not mailing_list.public:
            raise HTTPException(status_code=403, detail="Subscribing is not allowed")
        pending = await _get_pending(id, token, "subscribe")
        try:
            await add_external_member(mailing_list.principal_id, pending.email)
        except Exception as e:
            log.error("Failed to add member %s to list %s: %s", pending.email, id, e)
            raise HTTPException(status_code=502, detail=f"Stalwart error: {e}")
        await pending.delete()
        return {"detail": "Subscription confirmed"}


@route("/mailinglists/{id}/unsubscribe", tags=tags)
class MailingListUnsubscribeAPI:
    @staticmethod
    @description("Request unsubscription")
    async def post(
        id: int,
        data: SubscriberAction,
        request: Request,
    ) -> dict[str, str]:
        mailing_list = await _get_list(id)
        if not mailing_list.public:
            raise HTTPException(status_code=403, detail="Unsubscribing is not allowed")

        try:
            pending = await PendingSubscriber.objects.filter(
                mailing_list_id=id, email=data.email, action="unsubscribe"
            ).get()
        except oxyde.NotFoundError:
            pending = await PendingSubscriber.objects.create(
                mailing_list=mailing_list,
                mailing_list_id=mailing_list.id,
                email=data.email,
                action="unsubscribe",
                token=str(uuid4()),
                created_at=datetime.utcnow(),
            )
        confirm_url = f"{request.base_url}api/v1/mailinglists/{id}/unsubscribe/{pending.token}"
        msg = unsubscribe_confirmation(mailing_list.name, mailing_list.address, confirm_url)
        msg["To"] = data.email
        try:
            sendmail([data.email], msg)
        except Exception as e:
            log.error("Failed to send unsubscribe confirmation to %s: %s", data.email, e)
            raise HTTPException(status_code=502, detail="Failed to send confirmation email")
        return {"detail": "Please check your email to confirm unsubscription"}


@route("/mailinglists/{id}/unsubscribe/{token}", tags=tags)
class MailingListUnsubscribeConfirmAPI:
    @staticmethod
    @description("Confirm unsubscription")
    async def get(id: int, token: str) -> dict[str, str]:
        mailing_list = await _get_list(id)
        if not mailing_list.public:
            raise HTTPException(status_code=403, detail="Unsubscribing is not allowed")
        pending = await _get_pending(id, token, "unsubscribe")
        try:
            await remove_external_member(mailing_list.principal_id, pending.email)
        except Exception as e:
            log.error("Failed to remove member %s from list %s: %s", pending.email, id, e)
            raise HTTPException(status_code=502, detail=f"Stalwart error: {e}")
        await pending.delete()
        return {"detail": "Unsubscription confirmed"}


@route("/mailinglists/{id}/moderation", tags=tags)
class MailingListModerationAPI:
    @staticmethod
    @description("Get pending moderation queue")
    async def get(
        id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        cur_user: User = Depends(mailinglist_perms),
    ) -> Page[ModerationMessageResponse]:
        _require_admin(cur_user)
        mailing_list = await _get_list(id)
        return await paginate(
            ModerationMessage.objects.filter(
                mailing_list_id=mailing_list.id, status="pending"
            ).order_by("-created_at"),
            page,
            perpage,
        )


@route("/mailinglists/{id}/moderation/{msg_id}/approve", tags=tags)
class MailingListApproveAPI:
    @staticmethod
    @description("Approve moderated message")
    async def post(
        id: int,
        msg_id: int,
        cur_user: User = Depends(mailinglist_perms),
    ) -> ModerationMessageResponse:
        _require_admin(cur_user)
        mailing_list = await _get_list(id)
        moderation_message = await _get_moderation(id, msg_id)
        try:
            await approve_message(mailing_list, moderation_message)
        except Exception as e:
            log.error("Failed to approve message %s: %s", msg_id, e)
            raise HTTPException(status_code=502, detail=f"Failed to approve: {e}")
        return ModerationMessageResponse.model_validate(moderation_message)


@route("/mailinglists/{id}/moderation/{msg_id}/reject", tags=tags)
class MailingListRejectAPI:
    @staticmethod
    @description("Reject moderated message")
    async def post(
        id: int,
        msg_id: int,
        cur_user: User = Depends(mailinglist_perms),
    ) -> ModerationMessageResponse:
        _require_admin(cur_user)
        moderation_message = await _get_moderation(id, msg_id)
        await reject_message(moderation_message)
        return ModerationMessageResponse.model_validate(moderation_message)


@route("/mailinglists/{id}/process", tags=tags)
class MailingListProcessAPI:
    @staticmethod
    @description("Poll list inbox and process messages")
    async def post(
        id: int,
        cur_user: User = Depends(mailinglist_perms),
    ) -> dict[str, int]:
        _require_admin(cur_user)
        mailing_list = await _get_list(id)
        try:
            stats = await process_mailing_list(mailing_list)
        except Exception as e:
            log.error("Failed to process mailing list %s: %s", id, e)
            raise HTTPException(status_code=502, detail=f"Processing failed: {e}")
        return stats


