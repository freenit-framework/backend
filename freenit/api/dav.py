import base64
import ipaddress
import logging
import urllib.parse

import httpx
from fastapi import Depends, HTTPException, Request, Response
from freenit.api.router import api
from freenit.permissions import profile_perms
from pydantic import BaseModel

from ..config import getConfig

config = getConfig()
log = logging.getLogger("dav")

tags = ["dav"]

DAV_METHODS = [
    "GET", "HEAD", "OPTIONS", "PUT", "DELETE",
    "PROPFIND", "PROPPATCH", "MKCOL", "MKCALENDAR", "REPORT",
    "COPY", "MOVE",
]

FILE_DAV_METHODS = [
    "GET", "HEAD", "OPTIONS", "PUT", "DELETE",
    "PROPFIND", "PROPPATCH", "MKCOL",
    "COPY", "MOVE",
]

FORWARD_REQUEST_HEADERS = [
    "Content-Type", "Depth", "Prefer",
    "If-Match", "If-None-Match", "Overwrite",
]

FORWARD_RESPONSE_HEADERS = [
    "Content-Type", "ETag", "DAV", "Allow",
    "Location", "Content-Disposition",
]

ICAL_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def _dav_auth(user_email: str) -> str:
    credentials = f"{user_email}%{config.stalwart_admin}:{config.stalwart_admin_pass}"
    return "Basic " + base64.b64encode(credentials.encode()).decode()


async def _current_user(user=Depends(profile_perms)):
    return user


def _dav_account(email: str) -> str:
    return urllib.parse.quote(email, safe="")


def _check_ssrf(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only http/https URLs are allowed")
    host = parsed.hostname
    if not host:
        raise HTTPException(status_code=400, detail="Invalid URL")
    blocked = {"localhost", "localhost.localdomain"}
    if host in blocked or host.endswith(".local"):
        raise HTTPException(status_code=400, detail="Internal URLs are not allowed")
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise HTTPException(status_code=400, detail="Private/internal URLs are not allowed")
    except ValueError:
        pass  # host is a hostname, not a numeric IP — basic checks above apply


async def _dav_proxy(request: Request, user, upstream_url: str) -> Response:
    headers = {"Authorization": _dav_auth(user.email)}
    for name in FORWARD_REQUEST_HEADERS:
        val = request.headers.get(name)
        if val:
            headers[name] = val

    destination = request.headers.get("Destination")
    if destination:
        headers["Destination"] = destination

    # Stream PUT to avoid buffering large uploads in memory
    if request.method == "PUT":
        content_length = request.headers.get("Content-Length")
        if content_length:
            headers["Content-Length"] = content_length
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method="PUT",
                url=upstream_url,
                content=request.stream(),
                headers=headers,
            )
    else:
        has_body = request.method in {
            "POST", "PROPFIND", "PROPPATCH", "REPORT", "MKCALENDAR", "MKCOL",
        }
        body = await request.body() if has_body else None
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method=request.method,
                url=upstream_url,
                content=body,
                headers=headers,
            )

    if resp.status_code >= 400:
        log.warning(
            "DAV proxy error: user=%s method=%s url=%s status=%s body=%s",
            user.email, request.method, upstream_url,
            resp.status_code, resp.text[:500],
        )

    response_headers = {}
    for name in FORWARD_RESPONSE_HEADERS:
        val = resp.headers.get(name)
        if val:
            response_headers[name] = val

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
    )


# CalDAV

@api.api_route("/cal", methods=DAV_METHODS, tags=tags)
async def cal_root(request: Request, user=Depends(_current_user)) -> Response:
    upstream = f"{config.stalwart_url}/dav/cal/{_dav_account(user.email)}/"
    log.debug("CalDAV root: user=%s method=%s", user.email, request.method)
    return await _dav_proxy(request, user, upstream)


@api.api_route("/cal/{path:path}", methods=DAV_METHODS, tags=tags)
async def cal_proxy(request: Request, path: str, user=Depends(_current_user)) -> Response:
    upstream = f"{config.stalwart_url}/dav/cal/{_dav_account(user.email)}/{path}"
    log.debug("CalDAV: user=%s method=%s path=%s", user.email, request.method, path)
    return await _dav_proxy(request, user, upstream)


# CardDAV

@api.api_route("/card", methods=DAV_METHODS, tags=tags)
async def card_root(request: Request, user=Depends(_current_user)) -> Response:
    upstream = f"{config.stalwart_url}/dav/card/{_dav_account(user.email)}/"
    log.debug("CardDAV root: user=%s method=%s", user.email, request.method)
    return await _dav_proxy(request, user, upstream)


@api.api_route("/card/{path:path}", methods=DAV_METHODS, tags=tags)
async def card_proxy(request: Request, path: str, user=Depends(_current_user)) -> Response:
    upstream = f"{config.stalwart_url}/dav/card/{_dav_account(user.email)}/{path}"
    log.debug("CardDAV: user=%s method=%s path=%s", user.email, request.method, path)
    return await _dav_proxy(request, user, upstream)


# WebDAV file storage

@api.api_route("/file", methods=FILE_DAV_METHODS, tags=tags)
async def file_root(request: Request, user=Depends(_current_user)) -> Response:
    upstream = f"{config.stalwart_url}/dav/file/{_dav_account(user.email)}/"
    log.debug("WebDAV root: user=%s method=%s", user.email, request.method)
    return await _dav_proxy(request, user, upstream)


@api.api_route("/file/{path:path}", methods=FILE_DAV_METHODS, tags=tags)
async def file_proxy(request: Request, path: str, user=Depends(_current_user)) -> Response:
    upstream = f"{config.stalwart_url}/dav/file/{_dav_account(user.email)}/{path}"
    log.debug("WebDAV: user=%s method=%s path=%s", user.email, request.method, path)
    return await _dav_proxy(request, user, upstream)


# iCal URL fetch

class ICalFetchRequest(BaseModel):
    url: str


@api.post("/cal/fetch-ical", tags=tags)
async def ical_fetch(body: ICalFetchRequest, user=Depends(_current_user)) -> Response:
    _check_ssrf(body.url)
    log.debug("iCal fetch: user=%s url=%s", user.email, body.url)
    try:
        async with httpx.AsyncClient(follow_redirects=True, max_redirects=5) as client:
            resp = await client.get(
                body.url,
                headers={"Accept": "text/calendar"},
                timeout=15,
            )
    except httpx.RequestError as e:
        log.warning("iCal fetch error: user=%s url=%s error=%s", user.email, body.url, e)
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {e}")

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code,
                            detail="Remote server returned an error")

    if len(resp.content) > ICAL_MAX_BYTES:
        raise HTTPException(status_code=413, detail="iCal file too large (max 10 MB)")

    return Response(
        content=resp.content,
        status_code=200,
        media_type="text/calendar",
    )
