import bonsai
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.config import getConfig
from freenit.decorators import description
from freenit.models.ldap.base import get_client
from freenit.models.pagination import Page
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
        users = await User.get_all()
        total = len(users)
        page = Page(total=total, page=1, pages=1, perpage=total, data=users)
        return page


@route("/users/{id}", tags=tags)
class UserDetailAPI:
    @staticmethod
    async def get(id, _: User = Depends(user_perms)) -> UserSafe:
        user = await User.get(id)
        return user

    @staticmethod
    async def patch(id, data: UserOptional, _: User = Depends(user_perms)) -> UserSafe:
        user = await User.get(id)
        update = {
            field: getattr(data, field)
            for field in data.__fields__
            if getattr(data, field) != ""
        }
        await user.update(active=user.userClass, **update)
        return user

    @staticmethod
    async def delete(id, _: User = Depends(user_perms)) -> UserSafe:
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


@route("/profile", tags=["profile"])
class ProfileDetailAPI:
    @staticmethod
    @description("Get my profile")
    async def get(user: User = Depends(profile_perms)) -> UserSafe:
        return user

    @staticmethod
    @description("Edit my profile")
    async def patch(
        data: UserOptional, user: User = Depends(profile_perms)
    ) -> UserSafe:
        update = {
            field: getattr(data, field)
            for field in data.__fields__
            if getattr(data, field) != ""
        }
        await user.update(active=user.userClass, **update)
        return user
