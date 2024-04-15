from typing import Generic, TypeVar

from bonsai import LDAPClient, LDAPSearchScope, errors
from bonsai.errors import AuthenticationError, InsufficientAccess, UnwillingToPerform
from fastapi import HTTPException
from pydantic import BaseModel, Field

from freenit.config import getConfig

T = TypeVar("T")
config = getConfig()


def get_client(credentials=None):
    client = LDAPClient(f"ldap://{config.ldap.host}", config.ldap.tls)
    if credentials is not None:
        username, domain = credentials.email.split("@")
        dn = config.ldap.base.format(username, domain)
        client.set_credentials("SIMPLE", user=dn, password=credentials.password)
    else:
        dn = config.ldap.service_dn
        client.set_credentials("SIMPLE", user=dn, password=config.ldap.service_pw)
    return client


async def save_data(data):
    client = get_client()
    async with client.connect(is_async=True) as conn:
        try:
            await conn.add(data)
        except InsufficientAccess:
            raise HTTPException(
                status_code=403, detail="No permission to create user"
            )


class LDAPBaseModel(BaseModel, Generic[T]):
    @classmethod
    def dbtype(cls):
        return "ldap"

    dn: str = Field("", description=("Distinguished name"))


class LDAPUserMixin:
    @classmethod
    async def _login(cls, credentials) -> dict:
        client = get_client(credentials)
        try:
            async with client.connect(is_async=True) as conn:
                username, domain = credentials.email.split("@")
                dn = config.ldap.base.format(username, domain)
                res = await conn.search(dn, LDAPSearchScope.BASE, "objectClass=person")
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        data = res[0]
        return data

    @classmethod
    async def login(cls, credentials):
        data = await cls._login(credentials)
        user = cls(
            dn=str(data["dn"]),
            email=credentials.email,
            sn=data["sn"][0],
            cn=data["cn"][0],
            uid=data["uid"][0],
        )
        return user

    @classmethod
    async def register(cls, credentials):
        client = get_client()
        username, domain = credentials.email.split("@")
        dn = config.ldap.base.format(username, domain)
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(dn, LDAPSearchScope.BASE, "objectClass=person")
                if len(res) > 0:
                    raise HTTPException(status_code=409, detail="User already exists")
        except UnwillingToPerform:
            raise HTTPException(status_code=409, detail="Can not bind to LDAP")
        except AuthenticationError:
            raise HTTPException(status_code=409, detail="Can not bind to LDAP")
        user = cls(
            dn=dn, uid=username, email=credentials.email, password=credentials.password
        )
        return user
