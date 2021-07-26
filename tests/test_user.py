import pytest
from freenit.models.user import UserModel


class TestUser():
    @pytest.mark.asyncio
    async def test_get_all(self, db_setup, user_factory):
        user = user_factory()
        await user.save()

    @pytest.mark.asyncio
    async def test_get_new(self, db_setup, user_factory):
        count = await UserModel.objects.count()
        assert count == 0
