import json
import socket

from fastapi.testclient import TestClient


class Client(TestClient):
    def url_for(self, name, host=socket.gethostname()):
        return f"http://{host}:5000/api/v1{name}"

    def get(self, endpoint):
        url = self.url_for(endpoint)
        return super().get(url, cookies=self.cookies)

    def post(self, endpoint, data=None):
        url = self.url_for(endpoint)
        response = super().post(
            url,
            json=data,
            headers=self.headers,
            cookies=self.cookies,
        )

        return response

    def put(self, endpoint, data=None):
        url = self.url_for(endpoint)
        response = super().put(url, json=data, cookies=self.cookies)
        return response

    def patch(self, endpoint, data=None):
        url = self.url_for(endpoint)
        response = super().patch(url, json=data, cookies=self.cookies)
        return response

    def delete(self, endpoint):
        url = self.url_for(endpoint)
        return super().delete(url, cookies=self.cookies)

    def login(self, user, endpoint="/auth/login"):
        data = {
            "email": user.email,
            "password": "Sekrit",
        }
        response = self.post(endpoint, data)
        setattr(self, "cookies", response.cookies)
        return response
