from .base import Base


class TestAuth(Base):
    def test_me(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('api_v0.auth_login', user, 'Sekrit')
        assert response.status_code == 200
        response = self.get('api_v0.me')
        assert response.status_code == 200

    def test_logout(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('api_v0.auth_login', user, 'Sekrit')
        assert response.status_code == 200
        response = self.post('api_v0.auth_logout', {})
        assert response.status_code == 200

    def test_refresh(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('api_v0.auth_login', user, 'Sekrit')
        assert response.status_code == 200
        response = self.post('api_v0.auth_refresh', {}, 'refresh')
        assert response.status_code == 200
