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
    userClass: list[str] = Field([], description=("User class"))
    roles: list = Field([], description=("Roles the user is a member of"))
    groups: list = Field([], description=("Groups the user is a member of"))
    uidNumber: int = Field(0, description=("User ID number"))
    gidNumber: int = Field(0, description=("Group ID number"))
    active: bool = Field(False, description=("Active user"))
    admin: bool = Field(False, description=("Admin user"))

    @classmethod
    async def _login(cls, credentials) -> dict:
        client = get_client(credentials)
        try:
            async with client.connect(is_async=True) as conn:
                username, domain = credentials.email.split("@")
                dn = config.ldap.userDN.format(username, domain)
                res = await conn.search(dn, LDAPSearchScope.BASE, "objectClass=person")
        except errors.ConnectionError:
            raise HTTPException(
                status_code=409, detail="Can not connect to LDAP server"
            )
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        data = res[0]
        return data

    async def _fill_groups(self):
        _, domain = self.email.split('@')
        classes = class2filter(config.ldap.groupClasses)
        dn = f"{config.ldap.domainDN.format(domain)},{config.ldap.roleBase}"
        client = get_client()
        async with client.connect(is_async=True) as conn:
            try:
                res = await conn.search(
                    dn,
                    LDAPSearchScope.SUB,
                    f"(&{classes}(memberUid={self.uidNumber}))",
                )
            except errors.AuthenticationError:
                raise HTTPException(status_code=403, detail="Failed to login")
        self.groups = [g["gidNumber"][0] for g in res]

    @classmethod
    async def login(cls, credentials):
        data = await cls._login(credentials)
        user = cls.from_entry(data)
        if user.active:
            return user
        raise HTTPException(status_code=403, detail="Failed to login")

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
            raise HTTPException(
                status_code=409, detail="Can not login as service to LDAP"
            )
        user = cls(
            dn=dn,
            cn="Common Name",
            sn="Surname",
            uid=username,
            email=credentials.email,
            userClass=[],
            uidNumber=65535,
            gidNumber=65535,
            roles=[],
            groups=[],
            active=False,
            admin=False,
        )
        return user

    @classmethod
    def from_entry(cls, entry, groups=[]) -> UserSafe:
        active = False
        admin = False
        userClass = entry.get("userClass", [])
        if "active" in userClass:
            userClass.remove("active")
            active = True
        if "admin" in userClass:
            userClass.remove("admin")
            admin = True
        user = cls(
            email=entry["mail"][0],
            sn=entry["sn"][0],
            cn=entry["cn"][0],
            dn=str(entry["dn"]),
            uid=entry["uid"][0],
            userClass=userClass,
            roles=entry.get("memberOf", []),
            groups=groups,
            uidNumber=entry["uidNumber"][0],
            gidNumber=entry["gidNumber"][0],
            active=active,
            admin=admin,
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
            await user._fill_groups()
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
        await user._fill_groups()
        return user

    @classmethod
    async def get_by_uid(cls, uid: int):
        client = get_client()
        async with client.connect(is_async=True) as conn:
            try:
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
        await user._fill_groups()
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
        await user._fill_groups()
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

            userClass = self.userClass.copy()
            if self.active:
                userClass.append("active")
            if self.admin:
                userClass.append("admin")
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

    async def update(
        self,
        active=None,
        admin=None,
        password=None,
        roles=None,
        userClass=None,
        **kwargs,
    ):
        client = get_client()
        async with client.connect(is_async=True) as conn:
            res = await conn.search(self.dn, LDAPSearchScope.BASE)
            data = res[0]
            for field in kwargs:
                if field == 'uidNumber' or field == 'gidNumber':
                    if kwargs[field] == 0:
                        continue
                data[field] = kwargs[field]
            uclass = self.userClass.copy()
            if self.active:
                uclass.append('active')
            if self.admin:
                uclass.append('admin')
            if active is not None:
                if active:
                    if 'active' not in uclass:
                        uclass.append('active')
                        self.active = True
                else:
                    if 'active' in uclass:
                        uclass.remove('active')
                        self.active = False
            if admin is not None:
                if admin:
                    if 'admin' not in uclass:
                        uclass.append('admin')
                        self.admin = True
                else:
                    if 'admin' in uclass:
                        uclass.remove('admin')
                        self.admin = False
            data["userClass"] = uclass
            await data.modify()
            if password is not None:
                await conn.modify_password(self.dn, password)
        for field in kwargs:
            if field == 'uidNumber' or field == 'gidNumber':
                if kwargs[field] == 0:
                    continue
            setattr(self, field, kwargs[field])

    async def destroy(self):
        client = get_client()
        async with client.connect(is_async=True) as conn:
            classes = class2filter(config.ldap.roleClasses)
            filter_exp = f"(&(uniqueMember={self.dn}){classes})"
            res = await conn.search(
                config.ldap.roleBase, LDAPSearchScope.SUB, filter_exp
            )
            for role in res:
                if len(role["uniqueMember"]) == 1:
                    raise ValueError(
                        f"Can not destroy user as it is only member of role {role.cn}!"
                    )
            classes = class2filter(config.ldap.groupClasses)
            filter_exp = f"(&(memberUid={self.uidNumber}){classes})"
            res = await conn.search(
                config.ldap.roleBase, LDAPSearchScope.SUB, filter_exp
            )
            for group in res:
                if len(group["memberUid"]) == 1:
                    await group.delete()
            res = await conn.search(self.dn, LDAPSearchScope.BASE)
            data = res[0]
            await data.delete()


class UserOptional(User):
    pass


UserOptionalPydantic = UserOptional
