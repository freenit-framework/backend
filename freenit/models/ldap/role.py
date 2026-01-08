from bonsai import LDAPEntry, LDAPSearchScope, errors
from fastapi import HTTPException
from pydantic import BaseModel, Field

from freenit.config import getConfig
from freenit.models.ldap.base import LDAPBaseModel, get_client, save_data, class2filter

config = getConfig()


class Role(LDAPBaseModel):
    cn: str = Field("", description=("Common name"))
    users: list = Field([], description=("Role members"))

    @classmethod
    def from_entry(cls, entry):
        return cls(
            cn=entry["cn"][0],
            dn=str(entry["dn"]),
            users=entry[config.ldap.roleMemberAttr],
        )

    @classmethod
    def create(cls, name):
        dn = config.ldap.roleDN.format(name)
        return Role(dn=dn, cn=name, users=[])

    @classmethod
    async def get(cls, name):
        classes = class2filter(config.ldap.roleClasses)
        client = get_client()
        dn = config.ldap.roleDN.format(name)
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(dn, LDAPSearchScope.SUB, f"(|{classes})")
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such role")
        if len(res) > 1:
            raise HTTPException(status_code=409, detail="Multiple roles found")
        return cls.from_entry(res[0])

    @classmethod
    async def get_all(cls):
        classes = class2filter(config.ldap.roleClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    config.ldap.roleBase,
                    LDAPSearchScope.SUB,
                    f"(|{classes})",
                )
                data = []
                for gdata in res:
                    role = cls.from_entry(gdata)
                    data.append(role)
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        return data

    async def save(self, user):
        data = LDAPEntry(self.dn)
        data["objectClass"] = config.ldap.roleClasses
        data[config.ldap.roleMemberAttr] = user.dn
        await save_data(data)
        self.users = [user.dn]

    async def add(self, user):
        classes = class2filter(config.ldap.roleClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(self.dn, LDAPSearchScope.BASE, f"(|{classes})")
                if len(res) < 1:
                    raise HTTPException(status_code=404, detail="No such role")
                if len(res) > 1:
                    raise HTTPException(status_code=409, detail="Multiple roles found")
                data = res[0]
                try:
                    data[config.ldap.roleMemberAttr].append(user.dn)
                except ValueError:
                    raise HTTPException(
                        status_code=409, detail="User is already member of the role"
                    )
                await data.modify()
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        self.users.append(user.dn)

    async def remove(self, user):
        classes = class2filter(config.ldap.roleClasses)
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(self.dn, LDAPSearchScope.BASE, f"(|{classes})")
                if len(res) < 1:
                    raise HTTPException(status_code=404, detail="No such role")
                if len(res) > 1:
                    raise HTTPException(status_code=409, detail="Multiple roles found")
                data = res[0]
                try:
                    data[config.ldap.roleMemberAttr].remove(user.dn)
                except ValueError:
                    raise HTTPException(
                        status_code=409, detail="User is not member of the role"
                    )
                await data.modify()
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        self.users.remove(user.dn)


class RoleCreate(BaseModel):
    name: str = Field(description=("Common name"))


RoleOptional = Role
