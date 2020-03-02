from .base import Base


class TestAuth(Base):
    def test_me(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('auth.login', user, 'Sekrit')
        assert response.status_code == 200
        response = self.get('profile.profile')
        assert response.status_code == 200

    def test_logout(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('auth.login', user, 'Sekrit')
        assert response.status_code == 200
        response = self.post('auth.logout', {})
        assert response.status_code == 200

    def test_refresh(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('auth.login', user, 'Sekrit')
        assert response.status_code == 200
        response = self.post('auth.refresh', {}, 'refresh')
        assert response.status_code == 200
