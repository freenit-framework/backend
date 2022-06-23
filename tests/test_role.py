import pytest

from freenit.models.role import Role
from freenit.models.user import User

from . import factories


@pytest.mark.asyncio
class TestRole:
    async def test_get_role_list(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        response = client.get(f"/roles")
        assert response.status_code == 200

    async def test_create_role(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        data = {"name": "myrole"}
        response = client.post(f"/roles", data=data)
        assert response.status_code == 200

    async def test_get_role_by_id(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        role: Role = factories.Role()
        await role.save()
        response = client.get(f"/roles/{role.id}")
        assert response.status_code == 200

    async def test_edit_role(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        role: Role = factories.Role()
        await role.save()
        data = {"name": "myrole"}
        response = client.patch(f"/roles/{role.id}", data=data)
        assert response.status_code == 200

    async def test_delete_role(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        role: Role = factories.Role()
        await role.save()
        response = client.delete(f"/roles/{role.id}")
        assert response.status_code == 200
