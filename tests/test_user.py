import pytest

from freenit.config import getConfig

from . import factories

config = getConfig()
auth = config.get_user()


class TestUser:
    # @pytest.mark.asyncio
    # async def test_get_me(self, client):
    #     # setup user
    #     user = factories.User()
    #     await user.save()
    #     client.login(user=user)

    #     response = client.get("/users/me")
    #     assert response.status_code == 200

    # @pytest.mark.asyncio
    # async def test_patch_me(self, client):

    #     # setup user
    #     user = factories.User()
    #     await user.save()
    #     client.login(user=user)

    #     data = {
    #         "password": "Sekrit",
    #         "email": "user1@example.com",
    #         "is_active": True,
    #         "is_verified": True,
    #     }
    #     response = client.patch("/users/me", data=data)
    #     assert response.status_code == 200
    #     assert response.json()["email"] == data["email"]

    @pytest.mark.asyncio
    async def test_get_user_list(self, client):
        # setup admin
        admin = factories.User()
        await admin.save()
        client.login(user=admin)

        response = client.get(f"/users")
        print("response", response)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client):
        # setup admin
        admin = factories.User()
        await admin.save()
        client.login(user=admin)

        response = client.get(f"/users/{admin.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_patch_user_by_id(self, client):
        # setup admin
        admin = factories.User()
        await admin.save()
        client.login(user=admin)

        data = {
            "password": "Sekrit",
            "email": "user2@example.com",
            "active": True,
        }
        response = client.patch(f"/users/{admin.id}", data=data)
        assert response.status_code == 200
        assert response.json()["email"] == data["email"]

    @pytest.mark.asyncio
    async def test_delete_user(self, client):
        # setup admin
        admin = factories.User()
        await admin.save()
        client.login(user=admin)

        # setup user
        user = factories.User()
        await user.save()

        response = client.delete(f"/users/{user.id}")
        assert response.status_code == 200
