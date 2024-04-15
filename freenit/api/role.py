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
        if Role.dbtype() == "ormar":
            return await paginate(Role.objects, page, perpage)
        elif Role.dbtype() == "bonsai":
            import bonsai

            from freenit.models.ldap.base import get_client

            client = get_client()
            try:
                async with client.connect(is_async=True) as conn:
                    res = await conn.search(
                        f"dc=group,dc=ldap",
                        bonsai.LDAPSearchScope.SUB,
                        "objectClass=groupOfUniqueNames",
                    )
            except bonsai.errors.AuthenticationError:
                raise HTTPException(status_code=403, detail="Failed to login")
            data = []
            for gdata in res:
                role = Role(
                    cn=gdata["cn"][0],
                    dn=str(gdata["dn"]),
                    uniqueMembers=gdata["uniqueMember"],
                )
                data.append(role)

            total = len(res)
            page = Page(total=total, page=1, pages=1, perpage=total, data=data)
            return page
        raise HTTPException(status_code=409, detail="Unknown group type")

    @staticmethod
    async def post(role: Role, user: User = Depends(role_perms)) -> RoleSafe:
        if Role.dbtype() == "ormar":
            await role.save()
        elif Role.dbtype() == "bonsai":
            import bonsai
            try:
                await role.create(user)
            except bonsai.errors.AlreadyExists:
                raise HTTPException(status_code=409, detail="Role already exists")
        return role


@route("/roles/{id}", tags=tags)
class RoleDetailAPI:
    @staticmethod
    async def get(id, _: User = Depends(role_perms)) -> RoleSafe:
        if Role.dbtype() == "ormar":
            try:
                role = await Role.objects.get(pk=id)
            except ormar.exceptions.NoMatch:
                raise HTTPException(status_code=404, detail="No such role")
            await role.load_all(follow=True)
            return role
        elif Role.dbtype() == "bonsai":
            role = await Role.get(id)
            return role
        raise HTTPException(status_code=409, detail="Unknown role type")

    async def patch(
        id, role_data: RoleOptional, _: User = Depends(role_perms)
    ) -> RoleSafe:
        if Role.dbtype() == "ormar":
            try:
                role = await Role.objects.get(pk=id)
            except ormar.exceptions.NoMatch:
                raise HTTPException(status_code=404, detail="No such role")
            await role.patch(role_data)
            return role
        raise HTTPException(status_code=409, detail=f"Role type {Role.dbtype()} doesn't support PATCH method")

    @staticmethod
    async def delete(id, _: User = Depends(role_perms)) -> RoleSafe:
        if Role.dbtype() == "ormar":
            try:
                role = await Role.objects.get(pk=id)
            except ormar.exceptions.NoMatch:
                raise HTTPException(status_code=404, detail="No such role")
            await role.delete()
            return role
        elif Role.dbtype() == "bonsai":
            import bonsai

            from freenit.models.ldap.base import get_client

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
                        uniqueMembers=existing["uniqueMember"],
                    )
                    await existing.delete()
                    return role
            except bonsai.errors.AuthenticationError:
                raise HTTPException(status_code=403, detail="Failed to login")
        raise HTTPException(status_code=409, detail="Unknown role type")


@route("/roles/{role_id}/{user_id}", tags=tags)
class RoleUserAPI:
    @staticmethod
    @description("Assign user to role")
    async def post(
        role_id, user_id, _: User = Depends(role_perms)
    ) -> UserSafe:
        if Role.dbtype() == "ormar":
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
        elif Role.dbtype() == "bonsai":
            user = await User.get(user_id)
            role = await Role.get(role_id)
            await role.add(user)
            return user
        raise HTTPException(status_code=409, detail="Unknown role type")

    @staticmethod
    @description("Deassign user to role")
    async def delete(
        role_id, user_id, _: User = Depends(role_perms)
    ) -> UserSafe:
        if Role.dbtype() == "ormar":
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
        elif Role.dbtype() == "bonsai":
            user = await User.get(user_id)
            role = await Role.get(role_id)
            await role.remove(user)
            return user
        raise HTTPException(status_code=409, detail="Unknown role type")
