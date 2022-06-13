from typing import List

import ormar
import ormar.exceptions
from fastapi import HTTPException, Request

from freenit.api.router import route
from freenit.auth import authorize, encrypt
from freenit.decorators import description
from freenit.models.user import User, UserOptional, UserSafe


@route("/users", tags=["user"])
class UserListAPI:
    @staticmethod
    @description("Get users")
    async def get(request: Request) -> List[UserSafe]:
        await authorize(request)
        return await User.objects.all()


@route("/users/{id}", tags=["user"])
class UserDetailAPI:
    @staticmethod
    async def get(id: int, request: Request) -> UserSafe:
        await authorize(request)
        try:
            user = await User.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        return user

    @staticmethod
    async def delete(id: int, request: Request) -> UserSafe:
        await authorize(request)
        try:
            user = await User.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        await user.delete()
        return user


@route("/profile", tags=["profile"])
class ProfileDetailAPI:
    @staticmethod
    @description("Get my user")
    async def get(request: Request) -> UserSafe:
        profile = await authorize(request)
        return profile

    @staticmethod
    @description("Edit my user")
    async def patch(data: UserOptional, request: Request) -> UserSafe:
        profile = await authorize(request)
        if data.password:
            data.password = encrypt(data.password)
        await profile.patch(data)
        return profile
