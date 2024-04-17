import bonsai
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.decorators import description
from freenit.models.ldap.base import get_client
from freenit.models.pagination import Page
from freenit.models.role import Role
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
        _: int = Header(default=10),
        user: User = Depends(role_perms),
    ) -> Page[RoleSafe]:
        data = await Role.get_all()
        total = len(data)
        page = Page(total=total, page=1, pages=1, perpage=total, data=data)
        return page

    @staticmethod
    async def post(role: Role, user: User = Depends(role_perms)) -> RoleSafe:
        try:
            await role.create(user)
        except bonsai.errors.AlreadyExists:
            raise HTTPException(status_code=409, detail="Role already exists")
        return role


@route("/roles/{id}", tags=tags)
class RoleDetailAPI:
    @staticmethod
    async def get(id, _: User = Depends(role_perms)) -> RoleSafe:
        role = await Role.get(id)
        return role

    @staticmethod
    async def delete(id, _: User = Depends(role_perms)) -> RoleSafe:
        client = get_client()
        try:
            async with client.connect(is_async=True) as conn:
                res = await conn.search(
                    id, bonsai.LDAPSearchScope.SUB, "objectClass=groupOfUniqueNames"
                )
                if len(res) < 1:
                    raise HTTPException(status_code=404, detail="No such role")
                if len(res) > 1:
                    raise HTTPException(status_code=409, detail="Multiple role found")
                existing = res[0]
                role = Role(
                    cn=existing["cn"][0],
                    dn=str(existing["dn"]),
                    users=existing["uniqueMember"],
                )
                await existing.delete()
                return role
        except bonsai.errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")


@route("/roles/{role_id}/{user_id}", tags=tags)
class RoleUserAPI:
    @staticmethod
    @description("Assign user to role")
    async def post(role_id, user_id, _: User = Depends(role_perms)) -> UserSafe:
        user = await User.get(user_id)
        role = await Role.get(role_id)
        await role.add(user)
        return user

    @staticmethod
    @description("Deassign user to role")
    async def delete(role_id, user_id, _: User = Depends(role_perms)) -> UserSafe:
        user = await User.get(user_id)
        role = await Role.get(role_id)
        await role.remove(user)
        return user
