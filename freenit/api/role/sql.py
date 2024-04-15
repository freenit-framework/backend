import ormar
import ormar.exceptions
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.decorators import description
from freenit.models.pagination import Page, paginate
from freenit.models.role import Role, RoleOptional
from freenit.models.safe import RoleSafe, UserSafe
from freenit.models.user import User
from freenit.permissions import role_perms

tags = ["role"]


@route("/roles", tags=tags)
class RoleListAPI:
    @staticmethod
    @description("Get roles")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(role_perms),
    ) -> Page[RoleSafe]:
        return await paginate(Role.objects, page, perpage)

    @staticmethod
    async def post(role: Role, _: User = Depends(role_perms)) -> RoleSafe:
        await role.save()
        return role


@route("/roles/{id}", tags=tags)
class RoleDetailAPI:
    @staticmethod
    async def get(id, _: User = Depends(role_perms)) -> RoleSafe:
        try:
            role = await Role.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such role")
        await role.load_all(follow=True)
        return role

    @staticmethod
    async def patch(
        id, role_data: RoleOptional, _: User = Depends(role_perms)
    ) -> RoleSafe:
        if Role.dbtype() == "sql":
            try:
                role = await Role.objects.get(pk=id)
            except ormar.exceptions.NoMatch:
                raise HTTPException(status_code=404, detail="No such role")
            await role.patch(role_data)
            return role
        raise HTTPException(
            status_code=409,
            detail=f"Role type {Role.dbtype()} doesn't support PATCH method",
        )

    @staticmethod
    async def delete(id, _: User = Depends(role_perms)) -> RoleSafe:
        try:
            role = await Role.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such role")
        await role.delete()
        return role


@route("/roles/{role_id}/{user_id}", tags=tags)
class RoleUserAPI:
    @staticmethod
    @description("Assign user to role")
    async def post(role_id, user_id, _: User = Depends(role_perms)) -> UserSafe:
        try:
            user = await User.objects.get(pk=user_id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        await user.load_all()
        for role in user.roles:
            if role.id == role_id:
                raise HTTPException(status_code=409, detail="User already assigned")
        try:
            role = await Role.objects.get(pk=role_id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such role")
        await user.roles.add(role)
        return user

    @staticmethod
    @description("Deassign user to role")
    async def delete(role_id, user_id, _: User = Depends(role_perms)) -> UserSafe:
        try:
            user = await User.objects.get(pk=user_id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such user")
        try:
            role = await Role.objects.get(pk=role_id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such role")
        await user.load_all()
        try:
            await user.roles.remove(role)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="User is not part of role")
        return user
