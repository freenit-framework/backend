import asyncio
import base64
import contextlib
import logging

import httpx
import websockets
from fastapi import Depends, Request, Response, WebSocket, WebSocketDisconnect
from freenit.api.router import api, route
from freenit.permissions import profile_perms

from ..config import getConfig

config = getConfig()
log = logging.getLogger("mail")

tags = ["mail"]


def _jmap_auth(user_email: str) -> str:
    credentials = f"{user_email}%{config.stalwart_admin}:{config.stalwart_admin_pass}"
    log.debug("JMAP impersonation: user=%s admin=%s", user_email, config.stalwart_admin)
    return "Basic " + base64.b64encode(credentials.encode()).decode()


async def _current_user(user=Depends(profile_perms)):
    return user


@route("/mail/jmap", tags=tags)
class JMAPProxy:
    @staticmethod
    async def post(request: Request, user=Depends(_current_user)) -> Response:
        body = await request.body()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{config.stalwart_url}/jmap",
                content=body,
                headers={
                    "Authorization": _jmap_auth(user.email),
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        if resp.status_code >= 400:
            log.warning("JMAP proxy error: user=%s status=%s body=%s",
                        user.email, resp.status_code, resp.text[:500])
        return Response(content=resp.content, status_code=resp.status_code,
                        media_type="application/json")


@route("/mail/jmap/session", tags=tags)
class JMAPSession:
    @staticmethod
    async def get(user=Depends(_current_user)) -> Response:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{config.stalwart_url}/jmap/session",
                headers={"Authorization": _jmap_auth(user.email),
                         "Accept": "application/json"},
            )
        if resp.status_code >= 400:
            log.warning("JMAP session error: user=%s status=%s body=%s",
                        user.email, resp.status_code, resp.text[:500])
        return Response(content=resp.content, status_code=resp.status_code,
                        media_type="application/json")


@route("/mail/jmap/upload/{account_id}", tags=tags)
class JMAPUpload:
    @staticmethod
    async def post(account_id: str, request: Request,
                   user=Depends(_current_user)) -> Response:
        content_type = request.headers.get("Content-Type", "application/octet-stream")
        body = await request.body()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{config.stalwart_url}/jmap/upload/{account_id}",
                content=body,
                headers={
                    "Authorization": _jmap_auth(user.email),
                    "Content-Type": content_type,
                },
            )
        if resp.status_code >= 400:
            log.warning("JMAP upload error: user=%s account=%s status=%s body=%s",
                        user.email, account_id, resp.status_code, resp.text[:500])
        return Response(content=resp.content, status_code=resp.status_code,
                        media_type="application/json")


@route("/mail/jmap/download/{account_id}/{blob_id}/{name}", tags=tags)
class JMAPDownload:
    @staticmethod
    async def get(account_id: str, blob_id: str, name: str,
                  user=Depends(_current_user)) -> Response:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{config.stalwart_url}/jmap/download/{account_id}/{blob_id}/{name}",
                headers={"Authorization": _jmap_auth(user.email)},
            )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "application/octet-stream"),
            headers={k: v for k, v in resp.headers.items()
                     if k.lower() == "content-disposition"},
        )


@api.websocket("/mail/jmap/ws")
async def jmap_ws(websocket: WebSocket, user=Depends(_current_user)):
    ws_url = (
        config.stalwart_url
        .replace("http://", "ws://")
        .replace("https://", "wss://")
        + "/jmap/ws"
    )
    try:
        async with websockets.connect(
            ws_url,
            additional_headers={"Authorization": _jmap_auth(user.email)},
            subprotocols=["jmap"],
        ) as upstream:
            await websocket.accept(subprotocol=upstream.subprotocol)
            async def client_to_upstream():
                with contextlib.suppress(WebSocketDisconnect, Exception):
                    while True:
                        msg = await websocket.receive_text()
                        await upstream.send(msg)

            async def upstream_to_client():
                with contextlib.suppress(Exception):
                    async for msg in upstream:
                        text = msg if isinstance(msg, str) else msg.decode()
                        await websocket.send_text(text)

            t1 = asyncio.create_task(client_to_upstream())
            t2 = asyncio.create_task(upstream_to_client())
            await asyncio.wait([t1, t2], return_when=asyncio.FIRST_COMPLETED)
            t1.cancel()
            t2.cancel()
    except Exception as e:
        log.warning("JMAP WS error: user=%s error=%s", user.email, e)
    finally:
        with contextlib.suppress(Exception):
            await websocket.close()
