import base64
import logging
from typing import Any

import httpx
from freenit.config import getConfig

config = getConfig()
log = logging.getLogger("stalwart")


def _admin_auth() -> str:
    credentials = f"{config.stalwart_admin}:{config.stalwart_admin_pass}"
    return "Basic " + base64.b64encode(credentials.encode()).decode()


def _jmap_auth(user_email: str) -> str:
    credentials = f"{user_email}%{config.stalwart_admin}:{config.stalwart_admin_pass}"
    return "Basic " + base64.b64encode(credentials.encode()).decode()


def _headers() -> dict[str, str]:
    return {
        "Authorization": _admin_auth(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _jmap_headers(user_email: str) -> dict[str, str]:
    return {
        "Authorization": _jmap_auth(user_email),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def create_inbox_account(name: str, address: str) -> int:
    payload = {
        "type": "individual",
        "name": name,
        "description": f"Mailing list inbox for {address}",
        "emails": [address],
        "secrets": [],
        "memberOf": [],
        "roles": [],
        "lists": [],
        "members": [],
        "enabledPermissions": [],
        "disabledPermissions": [],
        "externalMembers": [],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.stalwart_url}/api/principal",
            json=payload,
            headers=_headers(),
        )
    if resp.status_code >= 400:
        log.error("Failed to create inbox account %s: %s %s", address, resp.status_code, resp.text[:500])
        raise RuntimeError(f"Stalwart create inbox failed: {resp.text}")
    data = resp.json().get("data", {})
    principal_id = data if isinstance(data, int) else data.get("id")
    log.info("Created inbox account %s with principal id %s", address, principal_id)
    return principal_id


async def create_list_principal(name: str, address: str) -> int:
    payload = {
        "type": "list",
        "name": name,
        "description": f"Mailing list distribution for {address}",
        "emails": [address],
        "secrets": [],
        "memberOf": [],
        "roles": [],
        "lists": [],
        "members": [],
        "enabledPermissions": [],
        "disabledPermissions": [],
        "externalMembers": [],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.stalwart_url}/api/principal",
            json=payload,
            headers=_headers(),
        )
    if resp.status_code >= 400:
        log.error("Failed to create list principal %s: %s %s", address, resp.status_code, resp.text[:500])
        raise RuntimeError(f"Stalwart create list failed: {resp.text}")
    data = resp.json().get("data", {})
    principal_id = data if isinstance(data, int) else data.get("id")
    log.info("Created list principal %s with id %s", address, principal_id)
    return principal_id


async def create_archive_account(name: str, address: str) -> int:
    payload = {
        "type": "individual",
        "name": name,
        "description": f"Mailing list archive for {address}",
        "emails": [address],
        "secrets": [],
        "memberOf": [],
        "roles": [],
        "lists": [],
        "members": [],
        "enabledPermissions": [],
        "disabledPermissions": [],
        "externalMembers": [],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.stalwart_url}/api/principal",
            json=payload,
            headers=_headers(),
        )
    if resp.status_code >= 400:
        log.error("Failed to create archive account %s: %s %s", address, resp.status_code, resp.text[:500])
        raise RuntimeError(f"Stalwart create archive failed: {resp.text}")
    data = resp.json().get("data", {})
    principal_id = data if isinstance(data, int) else data.get("id")
    log.info("Created archive account %s with id %s", address, principal_id)
    return principal_id


async def delete_principal(principal_id: int) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{config.stalwart_url}/api/principal/{principal_id}",
            headers=_headers(),
        )
    if resp.status_code >= 400:
        log.error("Failed to delete principal %s: %s %s", principal_id, resp.status_code, resp.text[:500])
        raise RuntimeError(f"Stalwart delete principal failed: {resp.text}")


async def patch_principal(principal_id: int, patches: list[dict[str, Any]]) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{config.stalwart_url}/api/principal/{principal_id}",
            json=patches,
            headers=_headers(),
        )
    if resp.status_code >= 400:
        log.error("Failed to patch principal %s: %s %s", principal_id, resp.status_code, resp.text[:500])
        raise RuntimeError(f"Stalwart patch principal failed: {resp.text}")


async def add_external_member(list_principal_id: int, email: str) -> None:
    await patch_principal(list_principal_id, [
        {"action": "addItem", "field": "externalMembers", "value": email}
    ])


async def remove_external_member(list_principal_id: int, email: str) -> None:
    await patch_principal(list_principal_id, [
        {"action": "removeItem", "field": "externalMembers", "value": email}
    ])


async def jmap_request(account_email: str, method_calls: list[list[Any]]) -> dict[str, Any]:
    payload = {
        "using": [
            "urn:ietf:params:jmap:core",
            "urn:ietf:params:jmap:mail",
        ],
        "methodCalls": method_calls,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.stalwart_url}/jmap",
            json=payload,
            headers=_jmap_headers(account_email),
        )
    if resp.status_code >= 400:
        log.error("JMAP request failed for %s: %s %s", account_email, resp.status_code, resp.text[:500])
        raise RuntimeError(f"JMAP request failed: {resp.text}")
    return resp.json()


async def fetch_mailbox_messages(account_email: str, role: str = "inbox") -> list[dict[str, Any]]:
    result = await jmap_request(account_email, [
        ["Mailbox/query", {"filter": {"role": role}}, "0"],
        ["Email/query", {
            "filter": {
                "inMailbox": "#{0}/ids[0]",
            },
            "sort": [{"property": "receivedAt", "isAscending": False}],
            "limit": 50,
        }, "1"],
    ])
    responses = {r[2]: r for r in result.get("methodResponses", [])}
    email_response = responses.get("1")
    if not email_response:
        return []
    _, data, _ = email_response
    return data.get("ids", [])


async def fetch_inbox_messages(account_email: str) -> list[dict[str, Any]]:
    return await fetch_mailbox_messages(account_email, "inbox")


async def fetch_email_bodies(account_email: str, email_id: str) -> dict[str, Any]:
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
    return data.get("list", [{}])[0]


async def fetch_email_summaries(account_email: str, email_ids: list[str]) -> list[dict[str, Any]]:
    if not email_ids:
        return []
    result = await jmap_request(account_email, [
        ["Email/get", {
            "ids": email_ids,
            "properties": ["id", "messageId", "subject", "from", "receivedAt"],
        }, "0"],
    ])
    responses = result.get("methodResponses", [])
    if not responses:
        return []
    _, data, _ = responses[0]
    return data.get("list", [])


async def destroy_emails(account_email: str, email_ids: list[str]) -> None:
    await jmap_request(account_email, [
        ["Email/set", {"destroy": email_ids}, "0"],
    ])


async def fetch_principal(principal_id: int) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{config.stalwart_url}/api/principal/{principal_id}",
            headers=_headers(),
        )
    if resp.status_code >= 400:
        log.error("Failed to fetch principal %s: %s %s", principal_id, resp.status_code, resp.text[:500])
        raise RuntimeError(f"Stalwart fetch principal failed: {resp.text}")
    return resp.json().get("data", {})


async def list_principals(types: str = "list", page: int = 1, limit: int = 100) -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{config.stalwart_url}/api/principal",
            params={"types": types, "page": page - 1, "limit": limit},
            headers=_headers(),
        )
    if resp.status_code >= 400:
        log.error("Failed to list principals: %s %s", resp.status_code, resp.text[:500])
        raise RuntimeError(f"Stalwart list principals failed: {resp.text}")
    return resp.json().get("data", {}).get("items", [])
