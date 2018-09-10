import pytest


@pytest.mark.usefixtures('client_class')
class TestDummy:
    def test_dummy(self, app, user_factory):
        user = user_factory()
        user.save()
        assert user.first_name == user.first_name
        #  assert user.first_name == self.client

    def test_another(self, app, user_factory):
        user = user_factory()
        user.save()
        assert len(user.__class__.select()) == 1
