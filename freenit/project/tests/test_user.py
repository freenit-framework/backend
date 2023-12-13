import pytest

from freenit.models.user import User

from . import factories


class TestUser:
    @pytest.mark.asyncio
    async def test_get_user_list(self, client):
        admin: User = factories.User()
        await admin.save()
        client.login(user=admin)
        response = client.get(f"/users")
        assert response.status_code == 200 #nosec
