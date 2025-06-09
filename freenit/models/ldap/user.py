from __future__ import annotations

from bonsai import LDAPEntry, LDAPModOp, LDAPSearchScope, errors
from fastapi import HTTPException
from pydantic import EmailStr, Field

from freenit.config import getConfig
from freenit.models.ldap.base import (
    LDAPBaseModel,
    class2filter,
    get_client,
    save_data,
    next_uid,
    next_gid,
)

config = getConfig()


class UserSafe(LDAPBaseModel):
    uid: str = Field("", description=("User ID"))
    email: EmailStr = Field("", description=("Email"))
    cn: str = Field("", description=("Common name"))
    sn: str = Field("", description=("Surname"))
    userClass: str = Field("", description=("User class"))
    roles: list = Field([], description=("Roles the user is a member of"))
    uidNumber: int = Field(0, description=("UID"))
    gidNumber: int = Field(0, description=("GID"))

    @classmethod
    async def _login(cls, credentials) -> dict:
        client = get_client(credentials)
        try:
            async with client.connect(is_async=True) as conn:
                username, domain = credentials.email.split("@")
                dn = config.ldap.userDN.format(username, domain)
                res = await conn.search(dn, LDAPSearchScope.BASE, "objectClass=person")
        except errors.ConnectionError:
            raise HTTPException(status_code=409, detail="Can not connect to LDAP server")
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        data = res[0]
        return data

    @classmethod
    async def login(cls, credentials):
        data = await cls._login(credentials)
        user = cls.from_entry(data)
        return user

    @classmethod
    async def register(cls, credentials):
        client = get_client()
        username, domain = credentials.email.split("@")
        dn = config.ldap.userDN.format(username, domain)
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(dn, LDAPSearchScope.BASE, "objectClass=person")
                if len(res) > 0:
                    raise HTTPException(status_code=409, detail="User already exists")
        except errors.UnwillingToPerform:
            raise HTTPException(status_code=409, detail="Can not bind to LDAP")
        except errors.AuthenticationError:
            raise HTTPException(status_code=409, detail="Can not bind to LDAP")
        user = cls(
            dn=dn,
            cn="Common Name",
            sn="Surname",
            uid=username,
            email=credentials.email,
            userClass="disabled",
            uidNumber=65535,
            gidNumber=65535,
            roles=[],
        )
        return user

    @classmethod
    def from_entry(cls, entry) -> UserSafe:
        user = cls(
            email=entry["mail"][0],
            sn=entry["sn"][0],
            cn=entry["cn"][0],
            dn=str(entry["dn"]),
            uid=entry["uid"][0],
            userClass=entry["userClass"][0],
            roles=entry.get("memberOf", []),
            uidNumber=entry["uidNumber"][0],
            gidNumber=entry["gidNumber"][0],
        )
        return user

    @classmethod
    async def get_all(cls):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    "dc=account,dc=ldap",
                    LDAPSearchScope.SUB,
                    "objectClass=person",
                    ["*", "memberOf"],
                )
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")

        data = []
        for udata in res:
            user = cls.from_entry(udata)
            data.append(user)
        return data

    @classmethod
    async def get(cls, dn):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    dn,
                    LDAPSearchScope.BASE,
                    "objectClass=person",
                    ["*", config.ldap.userMemberAttr],
                )
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login as a service")
        except errors.InvalidDN:
            raise HTTPException(status_code=409, detail=f"Invalid DN: {dn}")
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such user")
        if len(res) > 1:
            raise HTTPException(status_code=409, detail="Multiple users found")
        data = res[0]
        user = cls.from_entry(data)
        return user

    @classmethod
    async def get_by_uid(cls, uid: int):
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    config.ldap.userBase,
                    LDAPSearchScope.SUB,
                    f"(&(objectClass=person)(uidNumber={uid}))",
                    ["*", config.ldap.userMemberAttr],
                )
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such user")
        if len(res) > 1:
            raise HTTPException(status_code=409, detail="Multiple users found")
        user = cls.from_entry(res[0])
        return user

    @classmethod
    async def get_by_email(cls, email):
        client = get_client()
        username, domain = email.split("@")
        dn = config.ldap.userDN.format(username, domain)
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    dn,
                    LDAPSearchScope.BASE,
                    "objectClass=person",
                    ["*", config.ldap.userMemberAttr],
                )
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such user")
        if len(res) > 1:
            raise HTTPException(status_code=409, detail="Multiple users found")
        user = cls.from_entry(res[0])
        return user


class User(UserSafe):
    password: str = Field("", description=("Password"))

    async def save(self):
        try:
            uidNext = await next_uid()
            gidNext = await next_gid()
            _, domain = self.email.split("@")
            data = LDAPEntry(config.ldap.roleDN.format(self.uid, domain))
            data["objectClass"] = config.ldap.groupClasses
            data["cn"] = self.uid
            data["gidNumber"] = gidNext
            data["memberUid"] = uidNext
            await save_data(data)

            data = LDAPEntry(self.dn)
            data["objectClass"] = config.ldap.userClasses
            data["uid"] = self.uid
            data["cn"] = self.uid
            data["sn"] = self.uid
            data["uidNumber"] = uidNext
            data["gidNumber"] = gidNext
            data["userClass"] = self.userClass
            data["homeDirectory"] = f"/var/mail/domains/{domain}/{self.uid}"
            data.change_attribute("userPassword", LDAPModOp.REPLACE, (self.password,))
            data["mail"] = self.email
            await save_data(data)

            self.uidNumber = uidNext
            self.gidNumber = gidNext
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        client = get_client()
        async with client.connect(is_async=True) as conn:
            await conn.modify_password(self.dn, self.password)

    async def update(self, active=False, **kwargs):
        client = get_client()
        userClass = "disabled"
        if active:
            userClass = "enabled"
        special = {"password", "roles"}
        filtered = {x: kwargs[x] for x in kwargs if x not in special}
        async with client.connect(is_async=True) as conn:
            res = await conn.search(self.dn, LDAPSearchScope.BASE)
            data = res[0]
            if len(filtered.keys()) > 0:
                for field in filtered:
                    data[field] = filtered[field]
            password = kwargs.get("password", None)
            if password is not None:
                await conn.modify_password(self.dn, password)
            data["userClass"] = userClass
            data.change_attribute("userClass", LDAPModOp.REPLACE, userClass)
            self.userClass = userClass
            await data.modify()
        for field in filtered:
            setattr(self, field, filtered[field])

    async def destroy(self):
        client = get_client()
        async with client.connect(is_async=True) as conn:
            classes = class2filter(config.ldap.groupClasses)
            filter_exp=f"(&(memberUid={self.uidNumber}){classes})"
            res = await conn.search(config.ldap.roleBase, LDAPSearchScope.SUB, filter_exp)
            for group in res:
                if len(group['memberUid']):
                    await group.delete()
            classes = class2filter(config.ldap.roleClasses)
            filter_exp=f"(&(uniqueMember={self.dn}){classes})"
            res = await conn.search(config.ldap.roleBase, LDAPSearchScope.SUB, filter_exp)
            for role in res:
                if len(role['uniqueMember']):
                    raise ValueError(f"Can not destroy user as it is only member of role {role.cn}!")
            res = await conn.search(self.dn, LDAPSearchScope.BASE)
            data = res[0]
            await data.delete()


class UserOptional(User):
    pass


UserOptionalPydantic = UserOptional
