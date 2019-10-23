import json

import pytest
from flask import url_for
from werkzeug.datastructures import Headers


@pytest.mark.usefixtures('client_class')
class Base:
    headers = None

    def set_csrf(self, csrf_item=None):
        if csrf_item is not None:
            csrf_name = 'csrf_{}_token'.format(csrf_item)
            csrf = getattr(self, csrf_name)
            self.headers = Headers()
            self.headers.add_header('X-CSRF-TOKEN', csrf)

    def get(self, endpoint):
        url = url_for(endpoint)
        return self.client.get(url)

    def post(self, endpoint, data, csrf=None):
        url = url_for(endpoint)
        self.set_csrf(csrf)
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
            headers=self.headers,
        )
        self.headers = None
        return response

    def put(self, endpoint, data, csrf=None):
        url = url_for(endpoint)
        self.set_csrf(csrf)
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json',
            headers=self.headers,
        )
        self.headers = None
        return response

    def patch(self, endpoint, data, csrf=None):
        url = url_for(endpoint)
        self.set_csrf(csrf)
        response = self.client.patch(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        self.headers = None
        return response

    def delete(self, endpoint):
        url = url_for(endpoint)
        return self.client.patch(url)

    def login(self, endpoint, user, password):
        data = {
            'email': user.email,
            'password': password,
        }
        response = self.post(endpoint, data)
        cookies = [
            header for header in response.headers if header[0] == 'Set-Cookie'
        ]
        for cookie in cookies:
            name, value = cookie[1].split(';')[0].split('=')
            setattr(self, name, value)
        return response
