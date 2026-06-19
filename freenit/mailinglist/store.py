from freenit.models.mailinglist import MailingList

if MailingList.dbtype() == "sql":
    from .store_sql import (
        count_mailing_lists_by_addresses,
        create_mailing_list,
        create_moderation_message,
        create_pending_subscriber,
        delete_mailing_list,
        delete_pending_subscriber,
        get_mailing_list,
        get_moderation_message,
        get_pending_subscriber,
        get_pending_subscriber_by_email,
        list_mailing_lists,
        list_moderation_messages,
        save_moderation_message,
        update_mailing_list,
    )
elif MailingList.dbtype() == "ldap":
    from .store_ldap import (
        count_mailing_lists_by_addresses,
        create_mailing_list,
        create_moderation_message,
        create_pending_subscriber,
        delete_mailing_list,
        delete_pending_subscriber,
        get_mailing_list,
        get_moderation_message,
        get_pending_subscriber,
        get_pending_subscriber_by_email,
        list_mailing_lists,
        list_moderation_messages,
        save_moderation_message,
        update_mailing_list,
    )
else:
    raise RuntimeError(f"Unsupported mailing list backend: {MailingList.dbtype()}")

__all__ = [
    "count_mailing_lists_by_addresses",
    "create_mailing_list",
    "create_moderation_message",
    "create_pending_subscriber",
    "delete_mailing_list",
    "delete_pending_subscriber",
    "get_mailing_list",
    "get_moderation_message",
    "get_pending_subscriber",
    "get_pending_subscriber_by_email",
    "list_mailing_lists",
    "list_moderation_messages",
    "save_moderation_message",
    "update_mailing_list",
]
