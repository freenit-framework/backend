import pytest
from fastapi import HTTPException, Request

from freenit.auth import decode, encode, permissions
from freenit.models.group import Group, GroupUser
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
        group: Group = factories.Group()
        await group.save()
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
    async def test_group_fail_permissions(self, client):
        user: User = factories.User()
        await user.save()
        group: Group = factories.Group()
        await group.save()
        client.login(user=user)
        perms = permissions(groups=[group.name])
        request = prepareRequest(user)
        try:
            await perms(request)
        except HTTPException as e:
            assert e.detail == "Permission denied"
        else:
            pytest.fail("Permissions granted!")
