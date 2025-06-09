from typing import Generic, TypeVar

from bonsai import LDAPClient, LDAPSearchScope, errors
from fastapi import HTTPException
from pydantic import BaseModel, Field

from freenit.config import getConfig

T = TypeVar("T")
config = getConfig()


def get_client(credentials=None):
    client = LDAPClient(f"ldap://{config.ldap.host}", config.ldap.tls)
    if credentials is not None:
        username, domain = credentials.email.split("@")
        dn = config.ldap.userDN.format(username, domain)
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
        except errors.InsufficientAccess:
            raise HTTPException(status_code=403, detail="No permission to create group")


async def next_uid(increment=True) -> int:
    client = get_client()
    try:
        async with client.connect(is_async=True) as conn:
            res = await conn.search(
                config.ldap.uidNextDN,
                LDAPSearchScope.BASE,
                f"objectClass={config.ldap.uidNextClass}",
            )
            if len(res) < 1:
                raise HTTPException(status_code=404, detail="Can not find next UID")
            uidNext = int(res[0][config.ldap.uidNextField][0])
            if increment:
                res[0][config.ldap.uidNextField] = uidNext + 1
                await res[0].modify()
            return uidNext
    except errors.AuthenticationError:
        raise HTTPException(status_code=403, detail="Failed to login")


async def next_gid(increment=True):
    client = get_client()
    try:
        async with client.connect(is_async=True) as conn:
            res = await conn.search(
                config.ldap.gidNextDN,
                LDAPSearchScope.BASE,
                f"objectClass={config.ldap.gidNextClass}",
            )
            if len(res) < 1:
                raise HTTPException(status_code=404, detail="Can not find next GID")
            gidNext = int(res[0][config.ldap.gidNextField][0])
            if increment:
                res[0][config.ldap.gidNextField] = gidNext + 1
                await res[0].modify()
            return gidNext
    except errors.AuthenticationError:
        raise HTTPException(status_code=403, detail="Failed to login")


def class2filter(classes):
    return "".join([f"(objectClass={group})" for group in classes])


class LDAPBaseModel(BaseModel, Generic[T]):
    dn: str = Field("", description=("Distinguished name"))

    @classmethod
    def dbtype(cls):
        return "ldap"
