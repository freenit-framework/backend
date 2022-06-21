import pytest

from freenit.config import getConfig
from freenit.models.user import User

from . import factories

config = getConfig()


class TestUser:
    @pytest.mark.asyncio
    async def test_get_profile(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        response = client.get("/profile")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_patch_profile(self, client):
        admin: User = factories.User()
        await admin.save()
        client.login(user=admin)
        data = {
            "password": "Sekrit",
            "email": "user2@example.com",
        }
        response = client.patch("/profile", data=data)
        assert response.status_code == 200
        assert response.json()["email"] == data["email"]

    @pytest.mark.asyncio
    async def test_get_user_list(self, client):
        admin: User = factories.User()
        await admin.save()
        client.login(user=admin)
        response = client.get(f"/users")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client):
        admin: User = factories.User()
        await admin.save()
        client.login(user=admin)
        response = client.get(f"/users/{admin.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_user(self, client):
        admin: User = factories.User()
        await admin.save()
        client.login(user=admin)
        user: User = factories.User()
        await user.save()
        response = client.delete(f"/users/{user.id}")
        assert response.status_code == 200
