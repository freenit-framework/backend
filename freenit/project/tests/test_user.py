import pytest

from freenit.config import getConfig

config = getConfig()
auth = config.get_user()
UserModel = auth.UserModel


class TestUser:
    @pytest.mark.asyncio
    async def test_get_all(self, db_setup, user_factory):
        user = user_factory()
        await user.save()

    @pytest.mark.asyncio
    async def test_get_new(self, db_setup, user_factory):
        count = await UserModel.objects.count()
        assert count == 0
