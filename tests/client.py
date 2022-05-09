import json
import socket

from fastapi.testclient import TestClient


class Client(TestClient):
    def url_for(self, name, host=socket.gethostname()):
        return f"http://{host}:5000/api/v1{name}"

    def get_cookies(self):
        access = getattr(self, "access", "")
        refresh = getattr(self, "refresh", "")
        return {
            "access": access,
            "refresh": refresh,
        }

    def get(self, endpoint):
        url = self.url_for(endpoint)
        return super().get(url, cookies=self.get_cookies())

    def post(self, endpoint, data=None, type="json"):
        url = self.url_for(endpoint)
        response = super().post(
            url,
            data=json.dumps(data) if type == "json" else data,
            headers=self.headers,
            cookies=self.get_cookies(),
        )

        return response

    def put(self, endpoint, data=None):
        url = self.url_for(endpoint)
        response = super().put(
            url,
            data=json.dumps(data),
            cookies=self.get_cookies(),
        )
        return response

    def patch(self, endpoint, data=None):
        url = self.url_for(endpoint)
        response = super().patch(url, data=json.dumps(data), cookies=self.get_cookies())

        return response

    def delete(self, endpoint):
        url = self.url_for(endpoint)
        return super().delete(url, cookies=self.get_cookies())

    def login(self, user, endpoint="/auth/login"):
        data = {
            "email": user.email,
            "password": "Sekrit",
        }
        response = self.post(endpoint, data)
        cookies = response.headers.get("set-cookie", []).split(",")
        access = cookies[0].split(";")[0].strip().split("=")[1]
        refresh = cookies[1].split(";")[0].strip().split("=")[1]
        setattr(self, "access", access)
        setattr(self, "refresh", refresh)
        return response
