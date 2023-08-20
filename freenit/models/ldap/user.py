from __future__ import annotations

from bonsai import LDAPClient, LDAPSearchScope, errors
from fastapi import HTTPException
from pydantic import Field

from freenit.config import getConfig
from freenit.models.ldap.base import LDAPBaseModel, LDAPUserMixin

config = getConfig()


class UserSafe(LDAPBaseModel, LDAPUserMixin):
    @classmethod
    async def _login(cls, credentials) -> dict:
        username, domain = credentials.email.split("@")
        client = LDAPClient(f"ldap://{config.ldap.host}", config.ldap.tls)
        dn = config.ldap.base.format(username, domain)
        client.set_credentials("SIMPLE", user=dn, password=credentials.password)
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(dn, LDAPSearchScope.BASE, "objectClass=person")
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")

        data = res[0]
        return data

    @classmethod
    async def login(cls, credentials) -> UserSafe:
        data = await cls._login(credentials)
        user = cls(
            dn=str(data["dn"]),
            email=credentials.email,
            sn=data["sn"][0],
            cn=data["cn"][0],
            uid=data["uid"][0],
        )
        return user


class User(UserSafe):
    password: str = Field("", description=("Password"))


class UserOptional(User):
    pass


UserOptionalPydantic = UserOptional
