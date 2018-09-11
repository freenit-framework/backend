import json
import pytest
from flask_restplus.api import url_for


@pytest.mark.usefixtures('client_class')
class Base:
    def get(self, endpoint):
        url = url_for(endpoint)
        return self.client.get(url)

    def post(self, endpoint, data):
        url = url_for(endpoint)
        return self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def put(self, endpoint, data):
        url = url_for(endpoint)
        return self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def patch(self, endpoint, data):
        url = url_for(endpoint)
        return self.client.patch(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def delete(self, endpoint):
        url = url_for(endpoint)
        return self.client.patch(url)

    def login(self, endpoint, data):
        response = self.post(endpoint, data)
        cookies = [header for header in response.headers if header[0] == 'Set-Cookie']
        for cookie in cookies:
            name, value = cookie[1].split(';')[0].split('=')
            setattr(self, name, value)
        return response
