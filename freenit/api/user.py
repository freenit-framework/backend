import ormar
import ormar.exceptions
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.auth import encrypt
from freenit.config import getConfig
from freenit.decorators import description
from freenit.models.pagination import Page, paginate
from freenit.models.safe import UserSafe
from freenit.models.user import User, UserOptional
from freenit.permissions import profile_perms, user_perms

tags = ["user"]

config = getConfig()


@route("/users", tags=tags)
class UserListAPI:
    @staticmethod
    @description("Get users")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(user_perms),
    ) -> Page[UserSafe]:
        if User.dbtype() == "ormar":
            return await paginate(User.objects, page, perpage)
        elif User.dbtype() == "bonsai":
            import bonsai

            from freenit.models.ldap.base import get_client

            client = get_client()
            try:
                async with client.connect(is_async=True) as conn:
                    res = await conn.search(
                        f"dc=account,dc=ldap",
                        bonsai.LDAPSearchScope.SUB,
                        "objectClass=person",
                    )
            except bonsai.errors.AuthenticationError:
                raise HTTPException(status_code=403, detail="Failed to login")

            data = []
            for udata in res:
                email = udata.get("mail", None)
                if email is None:
                    continue
                user = User(
                    email=email[0],
                    sn=udata["sn"][0],
                    cn=udata["cn"][0],
                    dn=str(udata["dn"]),
                    uid=udata["uid"][0],
                )
                data.append(user)

            total = len(res)
            page = Page(total=total, page=1, pages=1, perpage=total, data=data)
            return page
        raise HTTPException(status_code=409, detail="Unknown user type")


@route("/users/{id}", tags=tags)
class UserDetailAPI:
    @staticmethod
    async def get(id, _: User = Depends(user_perms)) -> UserSafe:
        if User.dbtype() == "ormar":
            try:
                user = await User.objects.get(pk=id)
            except ormar.exceptions.NoMatch:
                raise HTTPException(status_code=404, detail="No such user")
            await user.load_all(follow=True)
            return user
        elif User.dbtype() == "bonsai":
            user = await User.get(id)
            return user
        raise HTTPException(status_code=409, detail="Unknown user type")

    @staticmethod
    async def patch(
        id, data: UserOptional, _: User = Depends(user_perms)
    ) -> UserSafe:
        if User.dbtype() == "ormar":
            if data.password:
                data.password = encrypt(data.password)
            try:
                user = await User.objects.get(pk=id)
            except ormar.exceptions.NoMatch:
                raise HTTPException(status_code=404, detail="No such user")
            await user.patch(data)
            return user
        elif User.dbtype() == "bonsai":
            user = await User.get(id)
            update = {
                field: getattr(data, field) for field in data.__fields__ if getattr(data, field) != ''
            }
            await user.update(active=user.userClass, **update)
            return user
        raise HTTPException(status_code=409, detail="Unknown user type")

    @staticmethod
    async def delete(id, _: User = Depends(user_perms)) -> UserSafe:
        if User.dbtype() == "ormar":
            try:
                user = await User.objects.get(pk=id)
            except ormar.exceptions.NoMatch:
                raise HTTPException(status_code=404, detail="No such user")
            await user.delete()
            return user
        elif User.dbtype() == "bonsai":
            import bonsai

            from freenit.models.ldap.base import get_client

            client = get_client()
            try:
                async with client.connect(is_async=True) as conn:
                    res = await conn.search(
                        id, bonsai.LDAPSearchScope.SUB, "objectClass=person"
                    )
                    if len(res) < 1:
                        raise HTTPException(status_code=404, detail="No such user")
                    if len(res) > 1:
                        raise HTTPException(status_code=409, detail="Multiple users found")
                    existing = res[0]
                    user = User(
                        email=existing["mail"][0],
                        sn=existing["sn"][0],
                        cn=existing["cn"][0],
                        dn=str(existing["dn"]),
                        uid=existing["uid"][0],
                        userClass=existing["userClass"][0],
                    )
                    await existing.delete()
                    return user
            except bonsai.errors.AuthenticationError:
                raise HTTPException(status_code=403, detail="Failed to login")
        raise HTTPException(status_code=409, detail="Unknown user type")


@route("/profile", tags=["profile"])
class ProfileDetailAPI:
    @staticmethod
    @description("Get my profile")
    async def get(user: User = Depends(profile_perms)) -> UserSafe:
        await user.load_all()
        return user

    @staticmethod
    @description("Edit my profile")
    async def patch(
        data: UserOptional, user: User = Depends(profile_perms)
    ) -> UserSafe:
        if data.password:
            data.password = encrypt(data.password)
        await user.patch(data)
        await user.load_all()
        return user
