import bonsai
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.config import getConfig
from freenit.decorators import description
from freenit.models.ldap.role import RoleCreate
from freenit.models.pagination import Page
from freenit.models.role import Role
from freenit.models.safe import RoleSafe
from freenit.models.user import User
from freenit.permissions import role_perms

tags = ["role"]
config = getConfig()


@route("/roles", tags=tags)
class RoleListAPI:
    @staticmethod
    @description("Get roles")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(role_perms),
    ) -> Page[RoleSafe]:
        data = await Role.get_all()
        perpage = len(data)
        data = Page(total=perpage, page=page, pages=1, perpage=perpage, data=data)
        return data

    @staticmethod
    async def post(data: RoleCreate, user: User = Depends(role_perms)) -> RoleSafe:
        if data.name == "":
            raise HTTPException(status_code=409, detail="Name is mandatory")
        role = Role.create(data.name)
        try:
            await role.save(user)
        except bonsai.errors.AlreadyExists:
            raise HTTPException(status_code=409, detail="Role already exists")
        return role


@route("/roles/{name}", tags=tags)
class RoleDetailAPI:
    @staticmethod
    async def get(name, _: User = Depends(role_perms)) -> RoleSafe:
        role = await Role.get(name)
        return role

    @staticmethod
    async def delete(name, _: User = Depends(role_perms)) -> RoleSafe:
        try:
            role = await Role.get(name)
            await role.destroy()
            return role
        except bonsai.errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")


@route("/roles/{role_name}/{id}", tags=tags)
class RoleUserAPI:
    @staticmethod
    @description("Assign user to role")
    async def post(role_name, id, _: User = Depends(role_perms)) -> RoleSafe:
        user = await User.get_by_uid(id)
        role = await Role.get(role_name)
        await role.add(user)
        return role

    @staticmethod
    @description("Remove user from role")
    async def delete(role_name, id, _: User = Depends(role_perms)) -> RoleSafe:
        user = await User.get_by_uid(id)
        role = await Role.get(role_name)
        if len(role.users) == 1:
            if role.users[0] == user.dn:
                raise HTTPException(status_code=409, detail="Can not remove last member")
        await role.remove(user)
        return role
