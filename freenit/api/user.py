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


@route("/users/{id}", tags=["user"], many=True)
class UserDetailAPI:
    @staticmethod
    async def get(id: int) -> User:
        try:
            user = await UserDB.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        return user

    @staticmethod
    async def patch(id: int, user_data: UserOptional) -> User:
        data = {}
        update_data = user_data.dict(exclude={"id", "password", "active"})
        for key in update_data:
            value = update_data[key]
            if value != None:
                data[key] = value
        try:
            user = await UserDB.objects.get(pk=id)
            await user.update(**data)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        return user

    @staticmethod
    async def delete(id: int) -> User:
        try:
            user = await UserDB.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        await user.delete()
        return user
