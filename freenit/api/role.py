from typing import List

import ormar
import ormar.exceptions
from fastapi import Depends, HTTPException

from freenit.api.router import route
from freenit.decorators import description
from freenit.models.role import Role, RoleOptional
from freenit.models.safe import RoleSafe, UserSafe
from freenit.models.user import User
from freenit.permissions import role_perms

tags = ["role"]


@route("/roles", tags=tags)
class RoleListAPI:
    @staticmethod
    @description("Get roles")
    async def get(_: User = Depends(role_perms)) -> List[RoleSafe]:
        return await Role.objects.select_all().exclude_fields(["password"]).all()

    @staticmethod
    async def post(role: Role, _: User = Depends(role_perms)) -> RoleSafe:
        await role.save()
        return role


@route("/roles/{id}", tags=tags)
class RoleDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(role_perms)) -> RoleSafe:
        try:
            role = await Role.objects.select_all().get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such role")
        return role

    @staticmethod
    async def patch(
        id: int, role_data: RoleOptional, _: User = Depends(role_perms)
    ) -> RoleSafe:
        try:
            role = await Role.objects.select_all().get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such role")
        await role.patch(role_data)
        return role

    @staticmethod
    async def delete(id: int, _: User = Depends(role_perms)) -> RoleSafe:
        try:
            role = await Role.objects.select_all().get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such role")
        await role.delete()
        return role


@route("/roles/{role_id}/{user_id}", tags=tags)
class RoleUserAPI:
    @staticmethod
    @description("Assign user to role")
    async def post(
        role_id: int, user_id: int, _: User = Depends(role_perms)
    ) -> UserSafe:
        try:
            user = await User.objects.select_all().get(pk=user_id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        for role in user.roles:
            if role.id == role_id:
                raise HTTPException(status_code=409, detail="User already assigned")
        try:
            role = await Role.objects.get(pk=role_id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such role")
        await user.roles.add(role)
        return user
