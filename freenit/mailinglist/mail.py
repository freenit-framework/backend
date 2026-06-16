from email.message import EmailMessage

from freenit.config import getConfig

config = getConfig()


def subscribe_confirmation(list_name: str, list_address: str, confirm_url: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = list_address
    msg["Subject"] = f"[{list_name}] Confirm subscription"
    msg.set_content(
        f"""Hello,

Please confirm your subscription to {list_name} <{list_address}> by visiting:

{confirm_url}

If you did not request this subscription, you can ignore this message.

Regards,
{config.name}
"""
    )
    return msg


def unsubscribe_confirmation(list_name: str, list_address: str, confirm_url: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = list_address
    msg["Subject"] = f"[{list_name}] Confirm unsubscription"
    msg.set_content(
        f"""Hello,

Please confirm that you want to unsubscribe from {list_name} <{list_address}> by visiting:

{confirm_url}

If you did not request this, you can ignore this message.

Regards,
{config.name}
"""
    )
    return msg


def moderation_notice(list_name: str, list_address: str, subject: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = list_address
    msg["Subject"] = f"[{list_name}] Your post is awaiting moderation"
    msg.set_content(
        f"""Hello,

Your message "{subject}" sent to {list_address} is awaiting moderator approval.

Regards,
{config.name}
"""
    )
    return msg
