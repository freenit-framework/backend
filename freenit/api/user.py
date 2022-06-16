from typing import List

import ormar
import ormar.exceptions
from fastapi import Depends, HTTPException

from freenit.api.router import route
from freenit.auth import encrypt
from freenit.decorators import description
from freenit.models.user import User, UserOptional, UserSafe
from freenit.permissions import profile_perms, user_perms


@route("/users", tags=["user"])
class UserListAPI:
    @staticmethod
    @description("Get users")
    async def get(_: User = Depends(user_perms)) -> List[UserSafe]:
        return await User.objects.all()


@route("/users/{id}", tags=["user"])
class UserDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(user_perms)) -> UserSafe:
        try:
            user = await User.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        return user

    @staticmethod
    async def delete(id: int, _: User = Depends(user_perms)) -> UserSafe:
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
    async def get(user: User = Depends(profile_perms)) -> UserSafe:
        return user

    @staticmethod
    @description("Edit my user")
    async def patch(
        data: UserOptional, user: User = Depends(profile_perms)
    ) -> UserSafe:
        if data.password:
            data.password = encrypt(data.password)
        await user.patch(data)
        return user
