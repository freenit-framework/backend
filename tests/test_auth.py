import pytest


class TestAuth():
    @pytest.mark.asyncio
    async def test_login(self, client, user_factory):
        user = user_factory()
        await user.save()
        response = client.login(user=user)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_logout(self, client, user_factory):
        user = user_factory()
        await user.save()
        client.login(user=user)

        response = client.post('logout', type='url')
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_register(self, client, user_factory):
        data = {
            "email": "user3@example.com",
            "password": "Sekrit",
        }
        response = client.post('register', data=data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_forgot_password(self, client, user_factory):
        user = user_factory()
        await user.save()
        client.login(user=user)

        response = client.post('forgot_password', data={'email': user.email})

        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_request_verify_token(self, client, user_factory):
        user = user_factory()
        await user.save()
        client.login(user=user)

        data = {'email': user.email}
        response = client.post('request_verify_token', data=data)

        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_reset_password(self, client, user_factory):
        pass  # TODO

    @pytest.mark.asyncio
    async def test_verify(self, client, user_factory):
        pass  # TODO
