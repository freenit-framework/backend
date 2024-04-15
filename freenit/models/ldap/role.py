from bonsai import LDAPEntry, LDAPSearchScope, errors
from fastapi import HTTPException
from pydantic import Field

from freenit.config import getConfig
from freenit.models.ldap.base import LDAPBaseModel, get_client, save_data

config = getConfig()


class Role(LDAPBaseModel):
    cn: str = Field("", description=("Common name"))
    users: list = Field([], description=("Role members"))

    @classmethod
    async def get(cls, dn):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    dn,
                    LDAPSearchScope.SUB,
                    "objectClass=groupOfUniqueNames",
                )
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such role")
        if len(res) > 1:
            raise HTTPException(status_code=409, detail="Multiple roles found")
        data = res[0]
        role = cls(
            cn=data["cn"][0],
            dn=str(data["dn"]),
            users=data["uniqueMember"],
        )
        return role

    @classmethod
    async def get_all(cls):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    f"dc=group,dc=ldap",
                    LDAPSearchScope.SUB,
                    "objectClass=groupOfUniqueNames",
                )
                data = []
                for gdata in res:
                    role = Role(
                        cn=gdata["cn"][0],
                        dn=str(gdata["dn"]),
                        users=gdata["uniqueMember"],
                    )
                    data.append(role)
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        return data


    async def create(self, user):
        data = LDAPEntry(self.dn)
        data["objectClass"] = config.ldap.groupClasses
        data["cn"] = self.cn
        data["uniqueMember"] = user.dn
        await save_data(data)
        self.users = data["uniqueMember"]

    async def add(self, user):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    self.dn, LDAPSearchScope.BASE, "objectClass=groupOfUniqueNames"
                )
                if len(res) < 1:
                    raise HTTPException(status_code=404, detail="No such role")
                if len(res) > 1:
                    raise HTTPException(status_code=409, detail="Multiple roles found")
                data = res[0]
                try:
                    data["uniqueMember"].append(user.dn)
                except ValueError:
                    raise HTTPException(status_code=409, detail="User is already member of the role")
                await data.modify()
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        self.users.append(user)

    async def remove(self, user):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    self.dn, LDAPSearchScope.BASE, "objectClass=groupOfUniqueNames"
                )
                if len(res) < 1:
                    raise HTTPException(status_code=404, detail="No such role")
                if len(res) > 1:
                    raise HTTPException(status_code=409, detail="Multiple roles found")
                data = res[0]
                try:
                    data["uniqueMember"].remove(user.dn)
                except ValueError:
                    raise HTTPException(status_code=409, detail="User is not member of the role")
                await data.modify()
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        self.users.remove(user)


RoleOptional = Role
