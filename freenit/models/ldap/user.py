from __future__ import annotations

from bonsai import LDAPEntry, LDAPModOp, LDAPSearchScope, errors
from fastapi import HTTPException
from pydantic import EmailStr, Field

from freenit.config import getConfig
from freenit.models.ldap.base import LDAPBaseModel, LDAPUserMixin, get_client, save_data

config = getConfig()


class UserSafe(LDAPBaseModel, LDAPUserMixin):
    uid: str = Field("", description=("User ID"))
    email: EmailStr = Field("", description=("Email"))
    cn: str = Field("", description=("Common name"))
    sn: str = Field("", description=("Surname"))
    userClass: str = Field("", description=("User class"))
    roles: list = Field([], description=("Roles the user is a member of"))


class User(UserSafe):
    password: str = Field("", description=("Password"))

    @classmethod
    async def get(cls, dn):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    dn, LDAPSearchScope.BASE,
                    "objectClass=person",
                    ["*", "memberOf"],
                )
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such user")
        if len(res) > 1:
            raise HTTPException(status_code=409, detail="Multiple users found")
        data = res[0]
        user = cls(
            email=data["mail"][0],
            sn=data["sn"][0],
            cn=data["cn"][0],
            dn=str(data["dn"]),
            uid=data["uid"][0],
            userClass=data["userClass"][0],
            roles=data.get("memberOf", []),
        )
        return user

    async def save(self):
        _, domain = self.email.split("@")
        data = LDAPEntry(self.dn)
        data["objectClass"] = config.ldap.userClasses
        data["uid"] = self.uid
        data["cn"] = self.uid
        data["sn"] = self.uid
        data["uidNumber"] = 65535
        data["gidNumber"] = 65535
        data["homeDirectory"] = f"/var/mail/domains/{domain}/{self.uid}"
        data.change_attribute("userPassword", LDAPModOp.REPLACE, self.password)
        data["mail"] = self.email
        await save_data(data)

    async def update(self, active=False, **kwargs):
        client = get_client()
        userclass = "disabled"
        if active:
            userclass = "enabled"
        async with client.connect(is_async=True) as conn:
            res = await conn.search(self.dn, LDAPSearchScope.BASE)
            data = res[0]
            data["userClass"] = userclass
            self.userClass = userclass
            for field in kwargs:
                data[field] = kwargs[field]
            await data.modify()
            for field in kwargs:
                setattr(self, field, kwargs[field])

    @classmethod
    async def get_all(cls):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    f"dc=account,dc=ldap",
                    LDAPSearchScope.SUB,
                    "objectClass=person",
                    ["*", "memberOf"],
                )
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")

        data = []
        for udata in res:
            email = udata.get("mail", None)
            if email is None:
                continue
            user = cls(
                email=email[0],
                sn=udata["sn"][0],
                cn=udata["cn"][0],
                dn=str(udata["dn"]),
                uid=udata["uid"][0],
                userClass=udata["userClass"][0],
                roles=udata.get("memberOf", []),
            )
            data.append(user)
        return data


class UserOptional(User):
    pass


UserOptionalPydantic = UserOptional
