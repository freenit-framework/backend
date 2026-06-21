#!/usr/bin/env python3
"""Git hook helper for Freenit-managed repositories.

This module is meant to be called from the git hooks of a bare repository:

    python -m freenit.git.hooks <repo-name> pre-receive
    python -m freenit.git.hooks <repo-name> update <ref> <oldrev> <newrev>
    python -m freenit.git.hooks <repo-name> post-receive

The pusher identity is taken from the FREENIT_PUSHER_EMAIL environment
variable, falling back to ``$USER@localhost``.
"""

import asyncio
import os
import subprocess  # nosec: B404
import sys
from typing import List, Tuple

from freenit.config import getConfig
from freenit.git import repo as git_repo
from freenit.git import store
from freenit.models.git import GitRepo

config = getConfig()


ACCESS_ORDER = {"read": 0, "write": 1, "admin": 2}


def _pusher_email() -> str:
    email = os.environ.get("FREENIT_PUSHER_EMAIL")
    if email:
        return email
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown"
    return f"{user}@localhost"


async def _ensure_db():
    if GitRepo.dbtype() == "sql" and not config.database.connected:
        await config.database.connect()


async def _get_repo_by_name(name: str) -> GitRepo:
    await _ensure_db()
    return await store.get_repo_by_name(name)


def _error(message: str) -> None:
    print(message, file=sys.stderr)


def _parse_ref_line(line: str) -> Tuple[str, str, str]:
    parts = line.strip().split(" ")
    if len(parts) != 3:
        raise ValueError(f"Invalid ref line: {line!r}")
    return parts[0], parts[1], parts[2]


def _refs_from_stdin() -> List[Tuple[str, str, str]]:
    refs = []
    for line in sys.stdin:
        if line.strip():
            refs.append(_parse_ref_line(line))
    return refs


def _is_deletion(new_rev: str) -> bool:
    return new_rev == "0" * len(new_rev)


def _is_creation(old_rev: str) -> bool:
    return old_rev == "0" * len(old_rev)


async def _check_write(repo: GitRepo, ref: str) -> bool:
    email = _pusher_email()
    allowed = await store.check_access(repo, email, "write")
    if not allowed:
        _error(f"User {email} does not have write access to {repo.name}")
    return allowed


async def pre_receive(repo_name: str) -> int:
    """Validate all refs in this push before accepting it."""
    try:
        repo = await _get_repo_by_name(repo_name)
    except Exception as exc:
        _error(f"Failed to load repository {repo_name}: {exc}")
        return 1

    refs = _refs_from_stdin()
    if not refs:
        return 0

    for _old, _new, ref in refs:
        if not await _check_write(repo, ref):
            return 1
    return 0


async def update(repo_name: str, ref: str, old_rev: str, new_rev: str) -> int:
    """Validate a single ref update."""
    try:
        repo = await _get_repo_by_name(repo_name)
    except Exception as exc:
        _error(f"Failed to load repository {repo_name}: {exc}")
        return 1

    if not await _check_write(repo, ref):
        return 1
    return 0


async def _run_tests_detached(repo_name: str, log_id: int) -> None:
    """Start a detached process that executes the tests."""
    subprocess.Popen(  # nosec
        [
            sys.executable,
            "-m",
            "freenit.git.hooks",
            "run-tests",
            repo_name,
            str(log_id),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


async def _record_task_refs(repo, old_rev: str, new_rev: str) -> None:
    try:
        commits = git_repo.walk_push_commits(repo.path, old_rev, new_rev)
    except Exception as exc:
        _error(f"Failed to walk commits for task refs: {exc}")
        return
    for commit in commits:
        for ref in git_repo.extract_task_refs(commit["message"]):
            try:
                await store.create_commit_task_ref(
                    repo=repo,
                    task_id=ref["task_id"],
                    commit_sha=commit["sha"],
                    relation=ref["relation"],
                )
            except Exception as exc:
                _error(
                    f"Failed to record task ref {ref['relation']} #{ref['task_id']}: {exc}"
                )


async def post_receive(repo_name: str) -> int:
    """Record pushes, trigger tests, and update task references."""
    try:
        repo = await _get_repo_by_name(repo_name)
    except Exception as exc:
        _error(f"Failed to load repository {repo_name}: {exc}")
        return 1

    refs = _refs_from_stdin()
    for old_rev, new_rev, ref in refs:
        try:
            push_log = await store.create_push_log(
                repo=repo,
                ref=ref,
                old_rev=old_rev,
                new_rev=new_rev,
                pusher_email=_pusher_email(),
                status="pending",
            )
            if repo.tests_enabled and repo.test_command:
                await _run_tests_detached(repo_name, push_log.id)
            else:
                await store.update_push_status(push_log, "completed")
            await _record_task_refs(repo, old_rev, new_rev)
        except Exception as exc:
            _error(f"Failed to record push for {ref}: {exc}")
    return 0


async def run_tests(repo_name: str, log_id: str) -> int:
    """Run the configured test command and update the push log."""
    try:
        await _ensure_db()
        repo = await _get_repo_by_name(repo_name)
        log = await store.get_push_log(int(log_id))
    except Exception as exc:
        _error(f"Failed to load repo/log: {exc}")
        return 1

    command = repo.test_command
    if not command:
        await store.update_push_status(log, "completed")
        return 0

    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=repo.path or None,
            check=False,
        )  # nosec
        output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}".strip()
        status = "success" if proc.returncode == 0 else "failure"
    except Exception as exc:
        output = str(exc)
        status = "failure"

    await store.update_push_status(log, status, output)
    return 0 if status == "success" else 1


async def main(argv: List[str]) -> int:
    if len(argv) < 2:
        _error("Usage: freenit.git.hooks <repo-name> <hook> [args...]")
        return 1

    repo_name = argv[0]
    hook = argv[1]
    args = argv[2:]

    await _ensure_db()

    if hook == "pre-receive":
        return await pre_receive(repo_name)
    if hook == "update":
        if len(args) != 3:
            _error("Usage: update <ref> <oldrev> <newrev>")
            return 1
        return await update(repo_name, args[0], args[1], args[2])
    if hook == "post-receive":
        return await post_receive(repo_name)
    if hook == "run-tests":
        if len(args) != 1:
            _error("Usage: run-tests <log-id>")
            return 1
        return await run_tests(repo_name, args[0])

    _error(f"Unknown hook: {hook}")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main(sys.argv[1:])))
    except KeyboardInterrupt:
        sys.exit(130)
