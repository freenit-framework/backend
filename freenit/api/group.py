from typing import List

import ormar
import ormar.exceptions
from fastapi import HTTPException, Request

from freenit.api.router import route
from freenit.auth import authorize
from freenit.decorators import description
from freenit.models.group import Group, GroupOptional, GroupUser, GroupUserSafe
from freenit.models.user import User


@route("/groups", tags=["group"])
class GroupListAPI:
    @staticmethod
    @description("Get groups")
    async def get(request: Request) -> List[Group]:
        await authorize(request)
        return await Group.objects.all()

    @staticmethod
    async def post(group: Group, request: Request) -> Group:
        await authorize(request)
        await group.save()
        return group


@route("/groups/{id}", tags=["group"])
class GroupDetailAPI:
    @staticmethod
    async def get(id: int, request: Request) -> Group:
        await authorize(request)
        try:
            group = await Group.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such group")
        return group

    @staticmethod
    async def patch(id: int, group_data: GroupOptional, request: Request) -> Group:
        await authorize(request)
        try:
            group = await Group.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such group")
        await group.patch(group_data)
        return group

    @staticmethod
    async def delete(id: int, request: Request) -> Group:
        await authorize(request)
        try:
            group = await Group.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such group")
        await group.delete()
        return group


@route("/groups/{group_id}/{user_id}", tags=["group"])
class GroupUserAPI:
    @staticmethod
    @description("Assign user to group")
    async def post(group_id: int, user_id: int, request: Request) -> GroupUserSafe:
        await authorize(request)
        try:
            group = await Group.objects.get(pk=group_id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such group")
        try:
            user = await User.objects.get(pk=user_id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        try:
            gu = await GroupUser.objects.get(group=group, user=user)
            raise HTTPException(status_code=409, detail="User already in the group")
        except ormar.exceptions.NoMatch:
            pass
        gu = GroupUser(user=user, group=group)
        await gu.save()
        return gu
