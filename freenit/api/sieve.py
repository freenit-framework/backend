import asyncio
import base64
import logging
from typing import List
from urllib.parse import urlparse

from fastapi import Depends, HTTPException
from freenit.api.router import route
from freenit.permissions import profile_perms
from pydantic import BaseModel

from ..config import getConfig

config = getConfig()
log = logging.getLogger("mail")

tags = ["mail"]

SIEVE_PORT = 4190


def _sieve_token(user_email: str) -> str:
    raw = f"\x00{user_email}%{config.stalwart_admin}\x00{config.stalwart_admin_pass}"
    return base64.b64encode(raw.encode()).decode()


def _sieve_host() -> str:
    return urlparse(config.stalwart_url).hostname


async def _current_user(user=Depends(profile_perms)):
    return user


class PutScriptBody(BaseModel):
    content: str


class ManageSieveClient:
    def __init__(self, host: str, port: int, token: str):
        self._host = host
        self._port = port
        self._token = token
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def __aenter__(self) -> "ManageSieveClient":
        self._reader, self._writer = await asyncio.open_connection(
            self._host, self._port
        )
        # Consume the server greeting (lines until OK)
        ok, _ = await self._read_response()
        if not ok:
            raise HTTPException(status_code=502, detail="ManageSieve greeting failed")
        # Authenticate
        cmd = f'AUTHENTICATE "PLAIN" "{self._token}"\r\n'
        self._writer.write(cmd.encode())
        await self._writer.drain()
        ok, lines = await self._read_response()
        if not ok:
            log.warning("ManageSieve auth failed: %s", lines)
            raise HTTPException(status_code=502, detail="ManageSieve authentication failed")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._writer is not None:
            try:
                self._writer.write(b"LOGOUT\r\n")
                await self._writer.drain()
                await self._read_response()
            except Exception as e:
                log.warning("ManageSieve LOGOUT error: %s", e)
            finally:
                self._writer.close()
                try:
                    await self._writer.wait_closed()
                except Exception as e:
                    log.warning("ManageSieve wait_closed error: %s", e)

    async def _read_response(self) -> tuple[bool, list[str]]:
        """Read lines until a terminal line (OK / NO / BYE).

        Handles RFC 5804 literal strings: a line of the form ``{NNN}`` or
        ``{NNN+}`` means the *next* NNN bytes are a literal (followed by CRLF
        that must be consumed).

        Returns (ok, collected_lines).
        """
        lines: list[str] = []
        while True:
            raw = await self._reader.readline()
            line = raw.decode(errors="replace").rstrip("\r\n")

            # Literal-length indicator
            if line.startswith("{") and (line.endswith("}") or line.endswith("+}")):
                inner = line.lstrip("{").rstrip("}").rstrip("+")
                try:
                    size = int(inner)
                except ValueError:
                    lines.append(line)
                    continue
                data = await self._reader.readexactly(size)
                # Consume trailing CRLF after the literal
                await self._reader.readline()
                lines.append(data.decode(errors="replace"))
                continue

            lines.append(line)

            upper = line.upper()
            if upper.startswith("OK"):
                return True, lines
            if upper.startswith("NO") or upper.startswith("BYE"):
                return False, lines

    async def list_scripts(self) -> list[dict]:
        self._writer.write(b"LISTSCRIPTS\r\n")
        await self._writer.drain()
        ok, lines = await self._read_response()
        if not ok:
            log.warning("ManageSieve LISTSCRIPTS failed: %s", lines)
            raise HTTPException(status_code=502, detail="LISTSCRIPTS failed")
        scripts = []
        for line in lines:
            upper = line.upper()
            if upper.startswith("OK"):
                break
            # Lines look like: "name" or "name" ACTIVE
            active = "ACTIVE" in upper
            # Strip surrounding quotes from the name
            name_part = line.split(" ACTIVE")[0].split(" active")[0].strip()
            name = name_part.strip('"')
            if name:
                scripts.append({"name": name, "active": active})
        return scripts

    async def get_script(self, name: str) -> tuple[str, bool]:
        cmd = f'GETSCRIPT "{name}"\r\n'
        self._writer.write(cmd.encode())
        await self._writer.drain()
        ok, lines = await self._read_response()
        if not ok:
            log.warning("ManageSieve GETSCRIPT %r failed: %s", name, lines)
            raise HTTPException(status_code=502, detail=f"GETSCRIPT {name!r} failed")
        # The literal content is the first non-OK line captured by _read_response
        content = ""
        for line in lines:
            if line.upper().startswith("OK"):
                break
            content = line
        # Determine active status via LISTSCRIPTS
        scripts = await self.list_scripts()
        active = any(s["name"] == name and s["active"] for s in scripts)
        return content, active

    async def put_script(self, name: str, content: str) -> None:
        encoded = content.encode()
        size = len(encoded)
        header = f'PUTSCRIPT "{name}" {{{size}+}}\r\n'
        self._writer.write(header.encode() + encoded + b"\r\n")
        await self._writer.drain()
        ok, lines = await self._read_response()
        if not ok:
            log.warning("ManageSieve PUTSCRIPT %r failed: %s", name, lines)
            raise HTTPException(status_code=502, detail=f"PUTSCRIPT {name!r} failed")

    async def delete_script(self, name: str) -> None:
        cmd = f'DELETESCRIPT "{name}"\r\n'
        self._writer.write(cmd.encode())
        await self._writer.drain()
        ok, lines = await self._read_response()
        if not ok:
            log.warning("ManageSieve DELETESCRIPT %r failed: %s", name, lines)
            raise HTTPException(status_code=502, detail=f"DELETESCRIPT {name!r} failed")

    async def set_active(self, name: str) -> None:
        cmd = f'SETACTIVE "{name}"\r\n'
        self._writer.write(cmd.encode())
        await self._writer.drain()
        ok, lines = await self._read_response()
        if not ok:
            log.warning("ManageSieve SETACTIVE %r failed: %s", name, lines)
            raise HTTPException(status_code=502, detail=f"SETACTIVE {name!r} failed")


def _client(user_email: str) -> ManageSieveClient:
    return ManageSieveClient(
        host=_sieve_host(),
        port=SIEVE_PORT,
        token=_sieve_token(user_email),
    )


@route("/mail/sieve/scripts", tags=tags)
class SieveScripts:
    @staticmethod
    async def get(user=Depends(_current_user)) -> List[dict]:
        async with _client(user.email) as sieve:
            return await sieve.list_scripts()


@route("/mail/sieve/scripts/{name}", tags=tags)
class SieveScript:
    @staticmethod
    async def get(name: str, user=Depends(_current_user)) -> dict:
        async with _client(user.email) as sieve:
            content, active = await sieve.get_script(name)
            return {"name": name, "content": content, "active": active}

    @staticmethod
    async def put(name: str, body: PutScriptBody, user=Depends(_current_user)) -> dict:
        async with _client(user.email) as sieve:
            await sieve.put_script(name, body.content)
            return {"name": name}

    @staticmethod
    async def delete(name: str, user=Depends(_current_user)) -> dict:
        async with _client(user.email) as sieve:
            await sieve.delete_script(name)
            return {"name": name}


@route("/mail/sieve/scripts/{name}/active", tags=tags)
class SieveScriptActive:
    @staticmethod
    async def post(name: str, user=Depends(_current_user)) -> dict:
        async with _client(user.email) as sieve:
            await sieve.set_active(name)
            return {"name": name, "active": True}

    @staticmethod
    async def delete(name: str, user=Depends(_current_user)) -> dict:
        async with _client(user.email) as sieve:
            await sieve.set_active("")
            return {"name": name, "active": False}
