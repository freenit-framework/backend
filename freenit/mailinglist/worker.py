import logging
from datetime import datetime
from email.message import EmailMessage
from typing import Any

from freenit.config import getConfig
from freenit.mail import sendmail
from freenit.models.sql.base import MailingList, ModerationMessage
from freenit.stalwart import (
    destroy_emails,
    fetch_email_bodies,
    jmap_request,
)

from .mail import moderation_notice

config = getConfig()
log = logging.getLogger("mailinglist.worker")


def _email_address(header_value: dict[str, Any] | list[dict[str, Any]] | None) -> str | None:
    if not header_value:
        return None
    if isinstance(header_value, list):
        header_value = header_value[0]
    return header_value.get("email") or header_value.get("address")


def _build_forward(original: dict[str, Any], list_address: str, distribution_address: str) -> EmailMessage:
    msg = EmailMessage()
    sender = _email_address(original.get("from")) or list_address
    msg["From"] = sender
    msg["To"] = distribution_address
    msg["Subject"] = original.get("subject", "")
    msg["List-Id"] = f"<{list_address}>"
    msg["Precedence"] = "list"
    msg["Reply-To"] = list_address

    text_body = original.get("textBody")
    html_body = original.get("htmlBody")

    if text_body and html_body:
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
    elif html_body:
        msg.add_alternative(html_body, subtype="html")
    elif text_body:
        msg.set_content(text_body)
    else:
        msg.set_content("")

    return msg


async def _fetch_inbox_email_ids(account_email: str) -> list[tuple[str, str]]:
    """Return list of (email_id, thread_id) for emails in the inbox."""
    result = await jmap_request(account_email, [
        ["Mailbox/query", {"filter": {"role": "inbox"}}, "0"],
        ["Email/query", {
            "filter": {
                "inMailbox": "#{0}/ids[0]",
            },
            "sort": [{"property": "receivedAt", "isAscending": False}],
            "limit": 100,
        }, "1"],
    ])
    responses = {r[2]: r for r in result.get("methodResponses", [])}
    email_response = responses.get("1")
    if not email_response:
        return []
    _, data, _ = email_response
    return [(item.get("id"), item.get("threadId")) for item in data.get("ids", [])]


async def _fetch_email_details(account_email: str, email_id: str) -> dict[str, Any]:
    result = await jmap_request(account_email, [
        ["Email/get", {
            "ids": [email_id],
            "properties": ["id", "messageId", "subject", "from", "receivedAt", "bodyValues"],
            "fetchAllBodyValues": True,
            "maxBodyValueBytes": 1048576,
        }, "0"],
    ])
    responses = result.get("methodResponses", [])
    if not responses:
        return {}
    _, data, _ = responses[0]
    items = data.get("list", [])
    return items[0] if items else {}


def _extract_bodies(email_data: dict[str, Any]) -> tuple[str | None, str | None]:
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
    return text_body, html_body


async def _store_moderation(mailing_list: MailingList, email_data: dict[str, Any], text_body: str | None, html_body: str | None) -> ModerationMessage:
    message_ids = email_data.get("messageId", [])
    message_id = message_ids[0] if isinstance(message_ids, list) and message_ids else None
    received_at = email_data.get("receivedAt")
    sent_at = datetime.fromisoformat(received_at.replace("Z", "+00:00")) if received_at else datetime.utcnow()
    return await ModerationMessage.objects.create(
        mailing_list=mailing_list,
        mailing_list_id=mailing_list.id,
        message_id=message_id,
        subject=email_data.get("subject"),
        sender=_email_address(email_data.get("from")),
        sent_at=sent_at,
        text_body=text_body,
        html_body=html_body,
        status="pending",
        created_at=datetime.utcnow(),
    )


async def _distribute(mailing_list: MailingList, email_data: dict[str, Any], text_body: str | None, html_body: str | None) -> None:
    original = {
        "from": email_data.get("from"),
        "subject": email_data.get("subject"),
        "textBody": text_body,
        "htmlBody": html_body,
    }
    msg = _build_forward(original, mailing_list.address, mailing_list.distribution_address)
    sendmail([mailing_list.distribution_address], msg)


async def process_mailing_list(mailing_list: MailingList) -> dict[str, int]:
    stats = {"distributed": 0, "moderated": 0, "errors": 0}
    if not mailing_list.inbox_principal_id:
        return stats

    try:
        email_ids = await _fetch_inbox_email_ids(mailing_list.address)
    except Exception as e:
        log.error("Failed to fetch inbox for %s: %s", mailing_list.address, e)
        return stats

    for email_id in email_ids:
        try:
            email_data = await _fetch_email_details(mailing_list.address, email_id)
            if not email_data:
                continue
            text_body, html_body = _extract_bodies(email_data)

            if mailing_list.moderation_enabled:
                await _store_moderation(mailing_list, email_data, text_body, html_body)
                stats["moderated"] += 1
                sender = _email_address(email_data.get("from"))
                if sender:
                    notice = moderation_notice(
                        mailing_list.name,
                        mailing_list.address,
                        email_data.get("subject", ""),
                    )
                    notice["To"] = sender
                    try:
                        sendmail([sender], notice)
                    except Exception as e:
                        log.warning("Failed to send moderation notice to %s: %s", sender, e)
            else:
                await _distribute(mailing_list, email_data, text_body, html_body)
                stats["distributed"] += 1

            await destroy_emails(mailing_list.address, [email_id])
        except Exception as e:
            log.error("Failed to process email %s for %s: %s", email_id, mailing_list.address, e)
            stats["errors"] += 1

    return stats


async def approve_message(mailing_list: MailingList, moderation_message: ModerationMessage) -> None:
    email_data = {
        "from": [{"email": moderation_message.sender}],
        "subject": moderation_message.subject,
        "messageId": [moderation_message.message_id] if moderation_message.message_id else [],
        "receivedAt": moderation_message.sent_at.isoformat() if moderation_message.sent_at else datetime.utcnow().isoformat(),
    }
    await _distribute(mailing_list, email_data, moderation_message.text_body, moderation_message.html_body)
    moderation_message.status = "approved"
    moderation_message.decided_at = datetime.utcnow()
    await moderation_message.save(update_fields=["status", "decided_at"])


async def reject_message(moderation_message: ModerationMessage) -> None:
    moderation_message.status = "rejected"
    moderation_message.decided_at = datetime.utcnow()
    await moderation_message.save(update_fields=["status", "decided_at"])
