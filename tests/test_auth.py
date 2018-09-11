from .base import Base


class TestAuth(Base):
    def test_login(self, app, user_factory):
        user = user_factory()
        user.save()
        data = {
            'email': user.email,
            'password': 'Sekrit',
        }
        response = self.login('api.auth_login', data)
        assert response.status_code == 200

    def test_empty_cookie(self, app, user_factory):
        user = user_factory()
        user.save()
        data = {
            'email': user.email,
            'password': 'Sekrit',
        }
        response = self.login('api.auth_login', data)
        assert response.status_code == 200
        #  assert getattr(self, 'access_token_cookie', None) == None
