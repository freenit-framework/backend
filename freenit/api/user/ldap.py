from bonsai import errors
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.config import getConfig
from freenit.decorators import description
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
        data = Page(total=total, page=1, pages=1, perpage=total, data=users)
        return data


@route("/users/{id}", tags=tags)
class UserDetailAPI:
    @staticmethod
    async def get(id, _: User = Depends(user_perms)) -> UserSafe:
        user = await User.get_by_uid(id)
        return user

    @staticmethod
    async def patch(id, data: UserOptional, _: User = Depends(user_perms)) -> UserSafe:
        user = await User.get_by_uid(id)
        update = {
            field: getattr(data, field)
            for field in data.__fields__
            if getattr(data, field) != ""
        }
        await user.update(**update)
        return user

    @staticmethod
    async def delete(id, _: User = Depends(user_perms)) -> UserSafe:
        try:
            user = await User.get_by_uid(id)
            await user.destroy()
        except errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")
        return user


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
        await user.update(**update)
        return user
