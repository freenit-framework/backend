import pytest
from fastapi import Cookie, Request

from freenit.auth import decode, encode, permissions
from freenit.models.group import Group
from freenit.models.user import User

from . import factories


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
        scope = {"type": "http"}
        request = Request(scope=scope)
        request._cookies = {"access": encode(user)}
        perms = permissions()
        token_user = await perms(request)
        assert user == token_user
