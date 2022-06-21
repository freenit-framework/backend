import pytest

from freenit.models.group import Group
from freenit.models.user import User

from . import factories


class TestGroup:
    @pytest.mark.asyncio
    async def test_get_group_list(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        response = client.get(f"/groups")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_group(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        data = {"name": "mygroup"}
        response = client.post(f"/groups", data=data)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_group_by_id(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        group: Group = factories.Group()
        await group.save()
        response = client.get(f"/groups/{group.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_edit_group(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        group: Group = factories.Group()
        await group.save()
        data = {"name": "mygroup"}
        response = client.patch(f"/groups/{group.id}", data=data)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_group(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        group: Group = factories.Group()
        await group.save()
        response = client.delete(f"/groups/{group.id}")
        assert response.status_code == 200
