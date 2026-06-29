import logging
from typing import Any

import httpx

from freenit.config import getConfig
from freenit.git import repo as git_repo

config = getConfig()
log = logging.getLogger("git.webhook")


def _clone_url(repo_name: str) -> str:
    host = config.hostname
    if config.port != 443 and config.port != 80:
        host = f"{host}:{config.port}"
    return f"https://{host}/git/{repo_name}"


async def notify_push(
    repo,
    ref: str,
    old_rev: str | None,
    new_rev: str | None,
    pusher_email: str,
) -> None:
    """Send a push event webhook payload to the repository's webhook URL."""
    url = getattr(repo, "webhook_url", None)
    if not url:
        return

    try:
        commits = git_repo.walk_push_commits(repo.path, old_rev, new_rev)
    except Exception as exc:
        log.warning("Failed to read commits for webhook: %s", exc)
        commits = []

    payload: dict[str, Any] = {
        "event": "push",
        "repository": {
            "id": repo.id,
            "name": repo.name,
            "url": _clone_url(repo.name),
        },
        "ref": ref,
        "before": old_rev,
        "after": new_rev,
        "pusher": {"email": pusher_email},
        "commits": commits,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except Exception as exc:
        log.warning("Webhook to %s failed: %s", url, exc)
