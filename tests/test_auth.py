import pytest

from freenit.models.user import User

from . import factories


class TestAuth:
    @pytest.mark.asyncio
    async def test_login(self, client):
        user: User = factories.User()
        await user.save()
        response = client.login(user=user)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_register(self, client):
        data = {
            "email": "user3@example.com",
            "password": "Sekrit",
        }
        response = client.post("/auth/register", data=data)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_refresh(self, client):
        user: User = factories.User()
        await user.save()
        client.login(user=user)
        response = client.post("/auth/refresh")
        assert response.status_code == 200
