from .base import Base


class TestUser(Base):
    def test_get_all(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('auth.login', user, 'Sekrit')
        assert response.status_code == 200
        response = self.get('users.list')
        assert response.status_code == 200

    def test_post(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('auth.login', user, 'Sekrit')
        assert response.status_code == 200
        data = {
            'email': 'some@example.com',
            'password': 'password',
        }
        response = self.post('users.list', data, 'access')
        assert response.status_code == 200
        json_data = response.get_json()
        assert data['email'] == json_data['email']
        newuser = user.get(id=json_data['id'])
        assert newuser.email == data['email']

    def test_get(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('auth.login', user, 'Sekrit')
        assert response.status_code == 200
        response = self.get('users.detail', user_id=user.id)
        assert response.status_code == 200

    def test_patch(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('auth.login', user, 'Sekrit')
        assert response.status_code == 200
        data = {
            'email': 'other@example.com',
        }
        response = self.patch('users.detail', data, 'access', user_id=user.id)
        assert response.status_code == 200
        user = user.get(id=user.id)
        assert user.email == data['email']

    def test_delete(self, user_factory):
        user = user_factory()
        user.save()
        response = self.login('auth.login', user, 'Sekrit')
        assert response.status_code == 200
        newuser = user_factory()
        newuser.save()
        response = self.delete('users.detail', 'access', user_id=newuser.id)
        assert response.status_code == 200
