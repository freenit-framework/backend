import pytest
from fastapi import HTTPException, Request

from freenit.auth import decode, encode, permissions
from freenit.models.role import Role
from freenit.models.user import User

from . import factories


def prepareRequest(user):
    scope = {"type": "http"}
    request = Request(scope=scope)
    request._cookies = {"access": encode(user)}
    return request


class TestPermission:
    @pytest.mark.asyncio
    async def test_encode_decode(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        role: Role = factories.Role()
        await role.save()
        token = encode(user)
        token_user = await decode(token)
        assert token_user == user

    @pytest.mark.asyncio
    async def test_permissions(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        perms = permissions()
        request = prepareRequest(user)
        token_user = await perms(request)
        assert user == token_user

    @pytest.mark.asyncio
    async def test_role_permissions(self, client):
        user: User = factories.User()
        await user.save()
        role: Role = factories.Role()
        await role.save()
        await user.roles.add(role)
        client.login(user=user)
        perms = permissions(roles=[role.name])
        request = prepareRequest(user)
        api_user = await perms(request)
        assert user == api_user

    @pytest.mark.asyncio
    async def test_role_fail_permissions(self, client):
        user: User = factories.User()
        await user.save()
        role: Role = factories.Role()
        await role.save()
        client.login(user=user)
        perms = permissions(roles=[role.name])
        request = prepareRequest(user)
        try:
            await perms(request)
        except HTTPException as e:
            assert e.detail == "Permission denied"
        else:
            pytest.fail("Permissions granted!")
        perms = permissions(allof=[role.name])
        try:
            await perms(request)
        except HTTPException as e:
            assert e.detail == "Permission denied"
        else:
            pytest.fail("Permissions granted!")
