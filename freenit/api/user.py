from typing import List

import ormar
import ormar.exceptions
from fastapi import HTTPException, Request

from freenit.api.router import route
from freenit.auth import authorize
from freenit.config import getConfig

config = getConfig()
auth = config.get_user()
UserDB = auth.User
UserOptional = auth.UserOptional
User = UserDB.get_pydantic(exclude={"password"})


@route("/users", tags=["user"], many=True)
class UserListAPI:
    @staticmethod
    async def get(request: Request) -> List[User]:
        await authorize(request)
        return await UserDB.objects.all()


@route("/users/{id}", tags=["user"])
class UserDetailAPI:
    @staticmethod
    async def get(id: int, request: Request) -> User:
        await authorize(request)
        try:
            user = await UserDB.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        return user

    @staticmethod
    async def delete(id: int, request: Request) -> User:
        await authorize(request)
        try:
            user = await UserDB.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        await user.delete()
        return user


@route("/profile", tags=["profile"])
class ProfileDetailAPI:
    @staticmethod
    async def get(request: Request) -> User:
        profile = await authorize(request)
        return profile

    @staticmethod
    async def patch(profile_data: UserOptional, request: Request) -> User:
        profile = await authorize(request)
        await profile.patch(profile_data)
        return profile
