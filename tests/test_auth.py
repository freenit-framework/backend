import pytest

from . import factories


@pytest.mark.asyncio
class TestAuth:
    async def test_login(self, client):
        user = factories.User()
        await user.save()
        response = client.login(user=user)

        assert response.status_code == 200

    async def test_register(self, client):
        data = {
            "email": "user3@example.com",
            "password": "Sekrit",
        }
        response = client.post("/auth/register", data=data)
        assert response.status_code == 200

    async def test_refresh(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        response = client.post("/auth/refresh")
        assert response.status_code == 200
