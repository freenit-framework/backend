import os
import re
from datetime import datetime, timedelta, timezone

from dulwich import errors as dulwich_errors
from dulwich.repo import Repo
from fastapi import HTTPException


def _ensure_repo(path: str) -> Repo:
    if not path or not os.path.isdir(path):
        raise HTTPException(status_code=404, detail="Repository path not found")
    try:
        return Repo(path)
    except dulwich_errors.NotGitRepository:
        raise HTTPException(status_code=404, detail="Not a git repository")


def _resolve_ref(repo: Repo, ref: str) -> bytes:
    try:
        return repo.refs[f"refs/heads/{ref}".encode()]
    except KeyError:
        pass
    try:
        return repo.refs[f"refs/tags/{ref}".encode()]
    except KeyError:
        pass
    # Allow full sha/ref names.
    try:
        return repo.refs[ref.encode()]
    except KeyError:
        pass
    try:
        return repo[ref.encode()].id
    except KeyError:
        raise HTTPException(status_code=404, detail="Ref not found")


def _commit_timestamp(commit) -> datetime | None:
    timestamp = getattr(commit, "commit_time", None)
    if timestamp is None:
        return None
    tz_offset = getattr(commit, "commit_timezone", 0)
    tz = timezone.utc if tz_offset == 0 else timezone(
        offset=timedelta(seconds=tz_offset)
    )
    return datetime.fromtimestamp(timestamp, tz=tz)


def _decode_message(message: bytes) -> str:
    return message.decode("utf-8", errors="replace")


def list_refs(path: str) -> list[dict]:
    repo = _ensure_repo(path)
    result = []
    for ref_name, sha in repo.refs.as_dict().items():
        if ref_name.startswith(b"refs/heads/") or ref_name.startswith(b"refs/tags/"):
            result.append({
                "name": ref_name.decode("utf-8", errors="replace"),
                "sha": sha.decode("ascii"),
            })
    result.sort(key=lambda r: r["name"])
    return result


def list_commits(path: str, ref: str, page: int, perpage: int) -> list[dict]:
    repo = _ensure_repo(path)
    sha = _resolve_ref(repo, ref)
    walker = repo.get_walker(include=[sha])
    commits = []
    for entry in walker:
        commit = entry.commit
        commits.append({
            "sha": entry.commit.id.decode("ascii"),
            "message": _decode_message(commit.message).strip(),
            "author": _decode_message(commit.author),
            "committer": _decode_message(commit.committer),
            "timestamp": _commit_timestamp(commit),
        })
    offset = (max(page, 1) - 1) * perpage
    return commits[offset : offset + perpage]


def _object_type(repo: Repo, sha: bytes) -> str:
    try:
        obj = repo[sha]
        return obj.type_name.decode("ascii")
    except KeyError:
        return "unknown"


def list_tree(path: str, ref: str, tree_path: str) -> list[dict]:
    repo = _ensure_repo(path)
    sha = _resolve_ref(repo, ref)
    commit = repo[sha]
    if commit.type_name != b"commit":
        raise HTTPException(status_code=400, detail="Ref is not a commit")
    tree = repo[commit.tree]
    if tree_path:
        parts = [p for p in tree_path.split("/") if p]
        for part in parts:
            found = False
            for name, mode, entry_sha in tree.iteritems():
                if name.decode("utf-8", errors="replace") == part:
                    child = repo[entry_sha]
                    if child.type_name != b"tree":
                        raise HTTPException(status_code=400, detail="Path is not a tree")
                    tree = child
                    found = True
                    break
            if not found:
                raise HTTPException(status_code=404, detail="Path not found")
    result = []
    for name, mode, entry_sha in tree.iteritems():
        result.append({
            "name": name.decode("utf-8", errors="replace"),
            "mode": oct(mode)[2:],
            "type": _object_type(repo, entry_sha),
            "sha": entry_sha.decode("ascii"),
        })
    result.sort(key=lambda e: (e["type"] != "tree", e["name"].lower()))
    return result


def get_blob(path: str, ref: str, blob_path: str) -> dict:
    repo = _ensure_repo(path)
    sha = _resolve_ref(repo, ref)
    commit = repo[sha]
    if commit.type_name != b"commit":
        raise HTTPException(status_code=400, detail="Ref is not a commit")
    tree = repo[commit.tree]
    parts = [p for p in blob_path.split("/") if p]
    if not parts:
        raise HTTPException(status_code=400, detail="Path is required")
    for part in parts[:-1]:
        found = False
        for name, mode, entry_sha in tree.iteritems():
            if name.decode("utf-8", errors="replace") == part:
                child = repo[entry_sha]
                if child.type_name != b"tree":
                    raise HTTPException(status_code=400, detail="Path is not a tree")
                tree = child
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail="Path not found")
    target_name = parts[-1]
    for name, mode, entry_sha in tree.iteritems():
        if name.decode("utf-8", errors="replace") == target_name:
            obj = repo[entry_sha]
            if obj.type_name != b"blob":
                raise HTTPException(status_code=400, detail="Path is not a file")
            data = obj.data
            return {
                "name": target_name,
                "sha": entry_sha.decode("ascii"),
                "size": len(data),
                "content": data.decode("utf-8", errors="replace"),
                "binary": b"\0" in data,
            }
    raise HTTPException(status_code=404, detail="File not found")


def get_readme(path: str, ref: str) -> dict | None:
    repo = _ensure_repo(path)
    sha = _resolve_ref(repo, ref)
    commit = repo[sha]
    if commit.type_name != b"commit":
        return None
    tree = repo[commit.tree]
    candidates = [b"README.md", b"README", b"readme.md", b"readme"]
    for candidate in candidates:
        for name, mode, entry_sha in tree.iteritems():
            if name == candidate:
                obj = repo[entry_sha]
                if obj.type_name == b"blob":
                    data = obj.data
                    return {
                        "name": candidate.decode("utf-8", errors="replace"),
                        "sha": entry_sha.decode("ascii"),
                        "content": data.decode("utf-8", errors="replace"),
                        "binary": b"\0" in data,
                    }
    return None


_FIX_RE = re.compile(r"(?:fixes|fix)\s*:\s*((?:#\d+(?:\s*,\s*#\d+)*))", re.IGNORECASE)
_REFER_RE = re.compile(r"(?:refers|refer)\s*:\s*((?:#\d+(?:\s*,\s*#\d+)*))", re.IGNORECASE)


def _extract_ids(text: str) -> list[int]:
    return [int(num) for num in re.findall(r"#(\d+)", text)]


def extract_task_refs(message: str) -> list[dict]:
    """Extract task references from a commit message.

    Supports patterns like:
        fixes: #1
        fixes: #1, #2, #3
        refer: #42
    """
    result = []
    for match in _FIX_RE.finditer(message):
        for task_id in _extract_ids(match.group(1)):
            result.append({"task_id": task_id, "relation": "fix"})
    for match in _REFER_RE.finditer(message):
        for task_id in _extract_ids(match.group(1)):
            result.append({"task_id": task_id, "relation": "refer"})
    return result


def walk_push_commits(
    path: str,
    old_rev: str | None,
    new_rev: str | None,
) -> list[dict]:
    """Return commits introduced by a push, each with sha and message."""
    repo = _ensure_repo(path)
    if not new_rev or new_rev == "0" * len(new_rev):
        return []
    new_sha = new_rev.encode("ascii")
    include = [new_sha]
    exclude = []
    if old_rev and old_rev != "0" * len(old_rev):
        exclude = [old_rev.encode("ascii")]
    walker = repo.get_walker(include=include, exclude=exclude)
    return [
        {
            "sha": entry.commit.id.decode("ascii"),
            "message": _decode_message(entry.commit.message),
        }
        for entry in walker
    ]
