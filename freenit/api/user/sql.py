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
        return await paginate(User.objects, page, perpage)


@route("/users/{id}", tags=tags)
class UserDetailAPI:
    @staticmethod
    async def get(id, _: User = Depends(user_perms)) -> UserSafe:
        try:
            user = await User.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        await user.load_all(follow=True)
        return user

    @staticmethod
    async def patch(id, data: UserOptional, _: User = Depends(user_perms)) -> UserSafe:
        if data.password:
            data.password = encrypt(data.password)
        try:
            user = await User.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        await user.patch(data)
        return user

    @staticmethod
    async def delete(id, _: User = Depends(user_perms)) -> UserSafe:
        try:
            user = await User.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        await user.delete()
        return user


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
