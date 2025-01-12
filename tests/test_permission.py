import pytest
from fastapi import HTTPException, Request
from freenit.auth import decode, encode, permissions

from . import factories


def prepareRequest(user):
    scope = {"type": "http"}
    request = Request(scope=scope)
    request._cookies = {"access": encode(user)}
    return request


@pytest.mark.asyncio
class TestPermission:
    async def test_encode_decode(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        role = factories.Role()
        await role.save()
        token = encode(user)
        token_user = await decode(token)
        assert token_user == user

    async def test_permissions(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        perms = permissions()
        request = prepareRequest(user)
        token_user = await perms(request)
        assert user == token_user

    async def test_role_permissions(self, client):
        user = factories.User()
        await user.save()
        role = factories.Role()
        await role.save()
        await user.roles.add(role)
        client.login(user=user)
        perms = permissions(roles=[role.name])
        request = prepareRequest(user)
        api_user = await perms(request)
        assert user == api_user

    async def test_role_fail_permissions(self, client):
        user = factories.User()
        await user.save()
        role = factories.Role()
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
