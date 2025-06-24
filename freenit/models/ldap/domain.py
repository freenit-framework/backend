from bonsai import LDAPEntry, LDAPSearchScope, errors
from fastapi import HTTPException
from pydantic import BaseModel, Field

from freenit.config import getConfig
from freenit.models.ldap.base import LDAPBaseModel, get_client, save_data, class2filter

config = getConfig()


class Domain(LDAPBaseModel):
    ou: str = Field("", description=("Domain name"))

    @classmethod
    def from_entry(cls, entry):
        domain = cls(dn=str(entry["dn"]), ou=entry["ou"][0])
        return domain

    @classmethod
    def create(cls, fqdn):
        dn = f"{config.ldap.domainDN},{config.ldap.roleBase}"
        rdomain = Domain(dn=dn.format(fqdn), ou=fqdn)
        dn = f"{config.ldap.domainDN},{config.ldap.userBase}"
        udomain = Domain(dn=dn.format(fqdn), ou=fqdn)
        return (rdomain, udomain)

    @classmethod
    async def get(cls, fqdn):
        classes = class2filter(config.ldap.domainClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                dn = f"{config.ldap.domainDN},{config.ldap.userBase}"
                res = await conn.search(dn.format(fqdn), LDAPSearchScope.SUB, f"(|{classes})")
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such domain")
        if len(res) > 1:
            raise HTTPException(status_code=409, detail="Multiple domains found")
        data = res[0]
        domain = cls.from_entry(data)
        return domain

    @classmethod
    async def get_rdomain(cls, fqdn):
        classes = class2filter(config.ldap.domainClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                dn = f"{config.ldap.domainDN},{config.ldap.roleBase}"
                res = await conn.search(dn.format(fqdn), LDAPSearchScope.SUB, f"(|{classes})")
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such domain")
        if len(res) > 1:
            raise HTTPException(status_code=409, detail="Multiple domains found")
        data = res[0]
        domain = cls.from_entry(data)
        return domain

    @classmethod
    async def get_all(cls):
        classes = class2filter(config.ldap.domainClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                dn = config.ldap.userBase
                res = await conn.search(dn, LDAPSearchScope.SUB, f"(|{classes})")
                data = []
                for gdata in res:
                    data.append(cls.from_entry(gdata))
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        return data

    async def save(self):
        data = LDAPEntry(self.dn)
        data["objectClass"] = config.ldap.domainClasses
        data["ou"] = self.ou
        await save_data(data)

    async def destroy(self):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                await conn.delete(self.dn)
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")


class DomainCreate(BaseModel):
    name: str = Field(description=("Common name"))
