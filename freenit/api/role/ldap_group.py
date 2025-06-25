import bonsai
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.config import getConfig
from freenit.decorators import description
from freenit.models.ldap.group import Group, GroupCreate
from freenit.models.pagination import Page
from freenit.models.user import User
from freenit.permissions import group_perms

tags = ["group"]
config = getConfig()


@route("/groups/{domain}", tags=tags)
class GroupListAPI:
    @staticmethod
    @description("Get groups")
    async def get(
        domain: str,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
    ) -> Page[Group]:
        data = await Group.get_all(domain)
        total = len(data)
        data = Page(total=total, page=1, pages=1, perpage=total, data=data)
        return data

    @staticmethod
    async def post(
        domain: str, data: GroupCreate, _: User = Depends(group_perms)
    ) -> Group:
        if data.name == "":
            raise HTTPException(status_code=409, detail="Name is mandatory")
        group = Group.create(data.name, domain)
        try:
            await group.save()
        except bonsai.errors.AlreadyExists:
            raise HTTPException(status_code=409, detail="Group already exists")
        return group


@route("/groups/{domain}/{name}", tags=tags)
class GroupDetailAPI:
    @staticmethod
    async def get(domain, name) -> Group:
        group = await Group.get(name, domain)
        return group

    @staticmethod
    async def delete(domain, name) -> Group:
        try:
            group = await Group.get(name, domain)
            await group.destroy()
            return group
        except bonsai.errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")


@route("/groups/{domain}/{name}/{uid}", tags=tags)
class GroupUserAPI:
    @staticmethod
    @description("Assign user to group")
    async def post(domain, name, uid, _: User = Depends(group_perms)) -> Group:
        user = await User.get_by_uid(uid)
        group = await Group.get(name, domain)
        await group.add(user)
        return group

    @staticmethod
    @description("Remove user from group")
    async def delete(domain, name, uid, _: User = Depends(group_perms)) -> Group:
        user = await User.get_by_uid(uid)
        group = await Group.get(name, domain)
        await group.remove(user)
        return group
