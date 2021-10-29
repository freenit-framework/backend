import pytest

from freenit.config import getConfig

config = getConfig()
auth = config.get_user()
UserModel = auth.UserModel


class TestUser:
    @pytest.mark.asyncio
    async def test_get_me(self, client, user_factory):

        # setup user
        user = user_factory()
        await user.save()
        client.login(user=user)

        response = client.get("me")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_patch_me(self, client, user_factory):

        # setup user
        user = user_factory()
        await user.save()
        client.login(user=user)

        data = {
            "password": "Sekrit",
            "email": "user1@example.com",
            "is_active": True,
            "is_verified": True,
        }
        response = client.patch("update_me", data=data)
        assert response.status_code == 200
        assert response.json()["email"] == data["email"]

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client, super_user_factory):

        # setup admin
        admin = super_user_factory()
        await admin.save()
        client.login(user=admin)

        response = client.get("get_user", id=str(admin.id))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_patch_user_by_id(self, client, super_user_factory):

        # setup admin
        admin = super_user_factory()
        await admin.save()
        client.login(user=admin)

        data = {
            "password": "Sekrit",
            "email": "user2@example.com",
            "is_active": True,
            "is_verified": True,
        }
        response = client.patch("update_user", data=data, id=str(admin.id))
        assert response.status_code == 200
        assert response.json()["email"] == data["email"]

    @pytest.mark.asyncio
    async def test_delete_user(self, client, super_user_factory, user_factory):

        # setup admin
        admin = super_user_factory()
        await admin.save()
        client.login(user=admin)

        # setup user
        user = user_factory()
        await user.save()

        response = client.delete("delete_user", id=str(user.id))
        assert response.status_code == 204
