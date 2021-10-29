import json
import socket
from fastapi.testclient import TestClient


class Client(TestClient):

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'accept': 'application/json'
    }

    def url_for(self, name, host=socket.gethostname(), **kwargs):
        return f'http://{host}:5000{self.app.url_path_for(name, **kwargs)}'
        # figure out how to get automaticly protocol/port

    def set_token(self, token_item=None):
        if token_item is None:
            token = getattr(self, 'token', '')
            self.headers.update({'Cookie': token})

    def get(self, endpoint, token=None, **kwargs):
        self.set_token(token)
        url = self.url_for(endpoint, **kwargs)
        return super().get(url, headers=self.headers)

    def post(self, endpoint, data=None, token=None, type='json', **kwargs):
        self.set_token(token)
        url = self.url_for(endpoint, **kwargs)
        response = super().post(
            url,
            data=json.dumps(data) if type == 'json' else data,
            headers=self.headers,
        )

        return response

    def put(self, endpoint, data=None, token=None, **kwargs):
        url = self.url_for(endpoint, **kwargs)
        self.set_token(token)
        response = super().put(
            url,
            data=json.dumps(data),
            headers=self.headers,
        )
        return response

    def patch(self, endpoint, data=None, token=None, **kwargs):
        url = self.url_for(endpoint, **kwargs)
        self.set_token(token)
        response = super().patch(
            url,
            data=json.dumps(data),
            headers=self.headers
        )

        return response

    def delete(self, endpoint, token=None, **kwargs):
        url = self.url_for(endpoint, **kwargs)
        self.set_token(token)
        return super().delete(url, headers=self.headers)

    def login(self, user, endpoint='login'):
        data = {
            'username': user.email,
            'password': 'Sekrit',
        }
        response = self.post(endpoint, data, type='url')
        value = response.headers.get('set-cookie', []).split(';')[0]
        setattr(self, 'token', value)
        return response
