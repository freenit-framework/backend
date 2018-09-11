import json
import pytest
from flask_restplus.api import url_for


@pytest.mark.usefixtures('client_class')
class Base:
    def get(self, endpoint, auth=None):
        url = url_for(endpoint)
        return self.client.get(url)

    def post(self, endpoint, data, auth=None):
        url = url_for(endpoint)
        return self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def put(self, endpoint, data, auth=None):
        url = url_for(endpoint)
        return self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def patch(self, endpoint, data, auth=None):
        url = url_for(endpoint)
        return self.client.patch(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def delete(self, endpoint, auth=None):
        url = url_for(endpoint)
        response = self.client.patch(url)
        return response

    def login(self, endpoint, user, password):
        data = {
            'email': user.email,
            'password': password,
        }
        response = self.post(endpoint, data)
        cookies = [header for header in response.headers if header[0] == 'Set-Cookie']
        for cookie in cookies:
            name, value = cookie[1].split(';')[0].split('=')
            setattr(self, name, value)
        return response
