from typing import List

from freenit.api.router import route

from ..models.user import User

# from fastapi import HTTPException


@route("/auth", tags=["auth"], many=True)
class AuthAPI:
    @staticmethod
    async def get() -> List[User]:
        return await User.objects.all()

    @staticmethod
    async def post(user: User) -> User:
        await user.save()
        return user
        # raise HTTPException(status_code=404, detail="No such user")
