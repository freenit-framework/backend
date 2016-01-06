import json
from unittest import TestCase
from base64 import b64encode
from flask import Flask

from app import create_app
from config import configs


class TestAPI(TestCase):
    def setUp(self):
        self.app = create_app(configs['testing'])
        self.app.db.cmd_migrate()
        self.app.test_request_context().push()
        self.client = self.app.test_client()

        from app import factories
        self.me = factories.UserFactory.create()
        self.me.save()

        admin_role = self.app.user_datastore.find_or_create_role(
            name="admin",
            description="Administrator"
        )
        self.app.user_datastore.add_role_to_user(self.me, admin_role)
        self.token = self.login(self.me.email, 'Sekrit')

    def login(self, email, password):
        response = self.client.post(
            '/api/v0/auth/tokens',
            data=json.dumps({'email': email, 'password': password}),
            content_type='application/json',
            follow_redirects=True,
        )
        json_response = json.loads(response.data)
        return json_response['token']

    def get(self, url):
        response = self.client.get(
            url,
            headers={
                'Authorization': 'JWT {token}'.format(token=self.token)
            },
        )
        self.assertLess(response.status_code, 400)
        data = json.loads(response.data)
        return data

    def post(self, url, data):
        response = self.client.post(
            url,
            data=json.dumps(data),
            headers={
                'Authorization': 'JWT {token}'.format(token=self.token),
                'Content-Type': 'application/json',
            },
        )
        self.assertLess(response.status_code, 400)
        return json.loads(response.data)

    def patch(self, url, data):
        response = self.client.patch(
            url,
            data=json.dumps(data),
            headers={
                'Authorization': 'JWT {token}'.format(token=self.token),
                'Content-Type': 'application/json',
            },
        )
        self.assertLess(response.status_code, 400)
        return json.loads(response.data)

    def delete(self, url):
        response = self.client.delete(
            url,
            headers={
                'Authorization': 'JWT {token}'.format(token=self.token)
            },
        )
        self.assertLess(response.status_code, 400)
        return json.loads(response.data)

    def test_user(self):
        from app import factories

        # Prepare
        user = factories.UserFactory.create()
        user.save()

        # Get details
        url_detail = 'api/v0/users/{pk}'.format(pk=user.id)
        response = self.get(url=url_detail)

        self.assertEqual(response['active'], user.active)
        self.assertEqual(response['admin'], user.admin)
        self.assertEqual(response['email'], user.email)
        self.assertEqual(response['confirmed_at'], user.confirmed_at)

