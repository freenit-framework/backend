import base64
import logging
import subprocess  # nosec: B404
from typing import Optional

import pydantic
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response as FastAPIResponse

from freenit.config import getConfig
from freenit.git import store
from freenit.models.user import User

config = getConfig()
log = logging.getLogger("git_http")

router = APIRouter()


class Credentials(pydantic.BaseModel):
    email: str
    password: str


def _packet_line(line: str) -> bytes:
    data = line.encode("utf-8")
    length = len(data) + 4
    return f"{length:04x}".encode("ascii") + data


def _service_command(service: str) -> str:
    if service == "git-upload-pack":
        return "upload-pack"
    if service == "git-receive-pack":
        return "receive-pack"
    raise HTTPException(status_code=400, detail="Invalid git service")


def _required_access(service: str) -> str:
    if service == "git-upload-pack":
        return "read"
    if service == "git-receive-pack":
        return "write"
    raise HTTPException(status_code=400, detail="Invalid git service")


async def _authenticate(request: Request) -> Optional[str]:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "basic" or not token:
        return None
    try:
        decoded = base64.b64decode(token).decode("utf-8")
    except Exception:
        return None
    email, _, password = decoded.partition(":")
    if not email or not password:
        return None
    try:
        user = await User.login(Credentials(email=email, password=password))
    except HTTPException:
        return None
    return user.email


def _basic_auth_challenge() -> FastAPIResponse:
    return FastAPIResponse(
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="git"'},
        content=b"Authentication required",
    )


async def _get_repo(repo_name: str):
    return await store.get_repo_by_name(repo_name)


async def _check_service_access(
    repo,
    service: str,
    user_email: Optional[str],
) -> None:
    required = _required_access(service)
    if required == "read" and repo.public and not user_email:
        return
    if not user_email:
        raise HTTPException(status_code=401, detail="Authentication required")
    allowed = await store.check_access(repo, user_email, required)
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/git/{repo_name}/info/refs")
async def git_info_refs(
    repo_name: str,
    service: str,
    request: Request,
):
    if not service:
        return FastAPIResponse(status_code=400, content=b"Service required")
    repo = await _get_repo(repo_name)
    user_email = await _authenticate(request)
    try:
        await _check_service_access(repo, service, user_email)
    except HTTPException as exc:
        if exc.status_code == 401:
            return _basic_auth_challenge()
        raise

    command = _service_command(service)
    try:
        proc = await __import__("asyncio").to_thread(
            subprocess.run,
            ["git", "-C", repo.path, command, "--advertise-refs", "."],
            capture_output=True,
            check=False,
        )  # nosec
    except Exception as exc:
        log.error("Failed to advertise refs for %s: %s", repo_name, exc)
        raise HTTPException(status_code=502, detail="Git backend error")

    if proc.returncode != 0:
        log.error("git advertise-refs failed: %s", proc.stderr.decode("utf-8", errors="replace"))
        raise HTTPException(status_code=502, detail="Git backend error")

    body = (
        _packet_line(f"# service={service}\n")
        + b"0000"
        + proc.stdout
    )
    return FastAPIResponse(
        content=body,
        media_type=f"application/x-{service}-advertisement",
    )


@router.post("/git/{repo_name}/git-upload-pack")
async def git_upload_pack(
    repo_name: str,
    request: Request,
    content_type: Optional[str] = Header(default=None),
):
    repo = await _get_repo(repo_name)
    user_email = await _authenticate(request)
    try:
        await _check_service_access(repo, "git-upload-pack", user_email)
    except HTTPException as exc:
        if exc.status_code == 401:
            return _basic_auth_challenge()
        raise

    body = await request.body()
    try:
        proc = await __import__("asyncio").to_thread(
            subprocess.run,
            ["git", "-C", repo.path, "upload-pack", "--stateless-rpc", "."],
            input=body,
            capture_output=True,
            check=False,
        )  # nosec
    except Exception as exc:
        log.error("Failed upload-pack for %s: %s", repo_name, exc)
        raise HTTPException(status_code=502, detail="Git backend error")

    return FastAPIResponse(
        content=proc.stdout,
        media_type="application/x-git-upload-pack-result",
    )


@router.post("/git/{repo_name}/git-receive-pack")
async def git_receive_pack(
    repo_name: str,
    request: Request,
    content_type: Optional[str] = Header(default=None),
):
    repo = await _get_repo(repo_name)
    user_email = await _authenticate(request)
    try:
        await _check_service_access(repo, "git-receive-pack", user_email)
    except HTTPException as exc:
        if exc.status_code == 401:
            return _basic_auth_challenge()
        raise

    body = await request.body()
    try:
        proc = await __import__("asyncio").to_thread(
            subprocess.run,
            ["git", "-C", repo.path, "receive-pack", "--stateless-rpc", "."],
            input=body,
            capture_output=True,
            check=False,
        )  # nosec
    except Exception as exc:
        log.error("Failed receive-pack for %s: %s", repo_name, exc)
        raise HTTPException(status_code=502, detail="Git backend error")

    return FastAPIResponse(
        content=proc.stdout,
        media_type="application/x-git-receive-pack-result",
    )
