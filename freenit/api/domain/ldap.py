import bonsai
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.config import getConfig
from freenit.decorators import description
from freenit.models.ldap.domain import Domain, DomainCreate
from freenit.models.pagination import Page
from freenit.models.user import User
from freenit.permissions import domain_perms

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
        data = Page(total=perpage, page=page, pages=1, perpage=perpage, data=data)
        return data

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
