from datetime import datetime

from fastapi import HTTPException

from freenit.models.mailinglist import (
    IntegrityError,
    MailingList,
    ModerationMessage,
    NotFoundError,
    PendingSubscriber,
)
from freenit.models.pagination import Page, paginate


async def get_mailing_list(id: int) -> MailingList:
    try:
        return await MailingList.objects.get(id=id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No such mailing list")


async def list_mailing_lists(
    page: int,
    perpage: int,
    public: bool | None = None,
) -> Page[MailingList]:
    query = MailingList.objects
    if public is not None:
        query = query.filter(public=public)
    return await paginate(query, page, perpage)


async def count_mailing_lists_by_addresses(addresses: list[str]) -> int:
    return await MailingList.objects.filter(address__in=addresses).count()


async def create_mailing_list(**kwargs) -> MailingList:
    try:
        return await MailingList.objects.create(**kwargs)
    except IntegrityError as e:
        raise HTTPException(
            status_code=409, detail=f"Mailing list already exists: {e}"
        )


async def update_mailing_list(mailing_list: MailingList, data) -> MailingList:
    await mailing_list.patch(data)
    return mailing_list


async def delete_mailing_list(mailing_list: MailingList) -> None:
    await mailing_list.delete()


async def get_pending_subscriber(
    mailing_list_id: int,
    token: str,
    action: str,
) -> PendingSubscriber:
    try:
        return await PendingSubscriber.objects.filter(
            mailing_list_id=mailing_list_id,
            token=token,
            action=action,
        ).get()
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Invalid or expired token")


async def get_pending_subscriber_by_email(
    mailing_list_id: int,
    email: str,
    action: str,
) -> PendingSubscriber:
    try:
        return await PendingSubscriber.objects.filter(
            mailing_list_id=mailing_list_id,
            email=email,
            action=action,
        ).get()
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Pending subscriber not found")


async def create_pending_subscriber(
    mailing_list: MailingList,
    email: str,
    action: str,
    token: str,
) -> PendingSubscriber:
    return await PendingSubscriber.objects.create(
        mailing_list=mailing_list,
        mailing_list_id=mailing_list.id,
        email=email,
        action=action,
        token=token,
        created_at=datetime.utcnow(),
    )


async def delete_pending_subscriber(pending: PendingSubscriber) -> None:
    await pending.delete()


async def get_moderation_message(
    mailing_list_id: int,
    msg_id: int,
) -> ModerationMessage:
    try:
        return await ModerationMessage.objects.filter(
            id=msg_id,
            mailing_list_id=mailing_list_id,
        ).get()
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No such moderation message")


async def list_moderation_messages(
    mailing_list_id: int,
    status: str,
    page: int,
    perpage: int,
) -> Page[ModerationMessage]:
    return await paginate(
        ModerationMessage.objects.filter(
            mailing_list_id=mailing_list_id,
            status=status,
        ).order_by("-created_at"),
        page,
        perpage,
    )


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
    return await ModerationMessage.objects.create(
        mailing_list=mailing_list,
        mailing_list_id=mailing_list.id,
        message_id=message_id,
        subject=subject,
        sender=sender,
        sent_at=sent_at,
        text_body=text_body,
        html_body=html_body,
        status=status,
        created_at=created_at,
    )


async def save_moderation_message(
    moderation_message: ModerationMessage,
    update_fields: list[str],
) -> None:
    await moderation_message.save(update_fields=update_fields)
