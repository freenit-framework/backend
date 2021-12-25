import pytest

from . import factories


class TestAuth:
    @pytest.mark.asyncio
    async def test_login(self, client):
        user = factories.User()
        await user.save()
        response = client.login(user=user)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_logout(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)

        response = client.post("/auth/logout", type="url")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_register(self, client):
        data = {
            "email": "user3@example.com",
            "password": "Sekrit",
        }
        response = client.post("/auth/register", data=data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_forgot_password(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)

        response = client.post("/auth/forgot-password", data={"email": user.email})

        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_request_verify_token(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)

        data = {"email": user.email}
        response = client.post("/auth/request-verify-token", data=data)
        assert response.status_code == 202
