import bonsai
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.config import getConfig
from freenit.decorators import description
from freenit.models.ldap.domain import Domain, DomainCreate
from freenit.models.ldap.group import Group, GroupCreate
from freenit.models.pagination import Page
from freenit.models.user import User
from freenit.models.safe import UserSafe
from freenit.permissions import domain_perms, group_perms

tags = ["domain"]
config = getConfig()


@route("/domains", tags=tags)
class DomainListAPI:
    @staticmethod
    @description("Get domains")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(domain_perms),
    ) -> Page[Domain]:
        data = await Domain.get_all()
        perpage = len(data)
        return Page(total=perpage, page=page, pages=1, perpage=perpage, data=data)

    @staticmethod
    async def post(data: DomainCreate, _: User = Depends(domain_perms)) -> Domain:
        if data.name == "":
            raise HTTPException(status_code=409, detail="Name is mandatory")
        rdomain, udomain = Domain.create(data.name)
        try:
            await rdomain.save()
            await udomain.save()
        except bonsai.errors.AlreadyExists:
            raise HTTPException(status_code=409, detail="Domain already exists")
        return udomain


@route("/domains/{name}", tags=tags)
class DomainDetailAPI:
    @staticmethod
    async def get(name, _: User = Depends(domain_perms)) -> Domain:
        domain = await Domain.get(name)
        return domain

    @staticmethod
    async def delete(name, _: User = Depends(domain_perms)) -> Domain:
        try:
            rdomain = await Domain.get_rdomain(name)
            await rdomain.destroy()
            domain = await Domain.get(name)
            await domain.destroy()
            return domain
        except bonsai.errors.AuthenticationError:
            raise HTTPException(status_code=403, detail="Failed to login")


@route("/domains/{name}/groups", tags=tags)
class DomainGroupListAPI:
    @staticmethod
    @description("Get groups")
    async def get(
        name,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(group_perms),
    ) -> Page[Group]:
        domain = await Domain.get(name)
        data = await Group.get_all(domain.ou)
        total = len(data)
        return Page(total=total, page=1, pages=1, perpage=total, data=data)

    @staticmethod
    @description("Create group")
    async def post(name, data: GroupCreate, _: User = Depends(group_perms)) -> Group:
        domain = await Domain.get(name)
        if data.name == "":
            raise HTTPException(status_code=409, detail="Name is mandatory")
        group = Group.create(domain.ou, data.name)
        try:
            await group.save()
        except bonsai.errors.AlreadyExists:
            raise HTTPException(status_code=409, detail="Group already exists")
        return group


@route("/domains/{name}/groups/{group}", tags=tags)
class DomainGroupDetailAPI:
    @staticmethod
    @description("Get group")
    async def get(name, group, _: User = Depends(group_perms)) -> Group:
        return await Group.get(group, name)

    @staticmethod
    @description("Destroy group")
    async def delete(name, group, _: User = Depends(group_perms)) -> Group:
        domain = await Domain.get(name)
        gr = await Group.get(group, domain.ou)
        gr.destroy()
        return gr


@route("/domains/{name}/groups/{group}/{uid}", tags=tags)
class GroupUserAPI:
    @staticmethod
    @description("Assign user to group")
    async def post(name, group, uid, _: User = Depends(group_perms)) -> Group:
        user = await User.get_by_uid(uid)
        gr = await Group.get(group, name)
        await gr.add(user)
        return gr

    @staticmethod
    @description("Remove user from group")
    async def delete(name, group, uid, _: User = Depends(group_perms)) -> Group:
        user = await User.get_by_uid(uid)
        gr = await Group.get(group, name)
        await gr.remove(user)
        return gr


@route("/domains/{name}/users", tags=tags)
class DomainUsersDetailAPI:
    @staticmethod
    @description("Get domain users")
    async def get(
        name,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(group_perms),
    ) -> Page[UserSafe]:
        data = await User.get_by_domain(name)
        perpage = len(data)
        return Page(total=perpage, page=page, pages=1, perpage=perpage, data=data)
