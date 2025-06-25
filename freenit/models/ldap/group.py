from bonsai import LDAPEntry, LDAPSearchScope, errors
from fastapi import HTTPException
from pydantic import BaseModel, Field

from freenit.config import getConfig
from freenit.models.ldap.base import LDAPBaseModel, get_client, save_data, class2filter

config = getConfig()


class Group(LDAPBaseModel):
    cn: str = Field("", description=("Common name"))
    users: list = Field([], description=("Group members"))

    @classmethod
    def from_entry(cls, entry):
        group = cls(
            cn=entry["cn"][0],
            dn=str(entry["dn"]),
            users=entry.get("memberUid", []),
        )
        return group

    @classmethod
    def create(cls, name, domain):
        group = Group(dn=config.ldap.groupDn.format(name, domain), cn=name, users=[])
        return group

    @classmethod
    async def get(cls, name, domain):
        classes = class2filter(config.ldap.groupClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                dn = config.ldap.groupDN.format(name, domain)
                res = await conn.search(dn, LDAPSearchScope.SUB, f"(|{classes})")
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such group")
        if len(res) > 1:
            raise HTTPException(status_code=409, detail="Multiple groups found")
        data = res[0]
        group = cls.from_entry(data)
        return group

    @classmethod
    async def get_all(cls, domain):
        classes = class2filter(config.ldap.groupClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                dn = config.ldap.roleBase.format(domain)
                res = await conn.search(dn, LDAPSearchScope.SUB, f"(|{classes})")
                data = []
                for gdata in res:
                    data.append(cls.from_entry(gdata))
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        return data

    async def save(self):
        data = LDAPEntry(self.dn)
        data["objectClass"] = config.ldap.groupClasses
        data["gidNumber"] = 0
        await save_data(data)

    async def destroy(self):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                await conn.delete(self.dn)
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")

    async def add(self, user):
        classes = class2filter(config.ldap.groupClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(self.dn, LDAPSearchScope.BASE, f"(|{classes})")
                if len(res) < 1:
                    raise HTTPException(status_code=404, detail="No such group")
                if len(res) > 1:
                    raise HTTPException(status_code=409, detail="Multiple groups found")
                data = res[0]
                try:
                    if "memberUid" not in data:
                        data["memberUid"] = []
                    data["memberUid"].append(user.uidNumber)
                except ValueError:
                    raise HTTPException(
                        status_code=409, detail="User is already member of the group"
                    )
                await data.modify()
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        self.users.append(user.uidNumber)

    async def remove(self, user):
        classes = class2filter(config.ldap.groupClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(self.dn, LDAPSearchScope.BASE, f"(|{classes})")
                if len(res) < 1:
                    raise HTTPException(status_code=404, detail="No such group")
                if len(res) > 1:
                    raise HTTPException(status_code=409, detail="Multiple groups found")
                data = res[0]
                try:
                    data["memberUid"].remove(user.uidNumber)
                except ValueError:
                    raise HTTPException(
                        status_code=409, detail="User is not member of the group"
                    )
                await data.modify()
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        self.users.remove(user.uidNumber)


class GroupCreate(BaseModel):
    name: str = Field(description=("Common name"))
