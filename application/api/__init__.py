from flask import render_template
from flask_rest_api import Api


class MyAPI(Api):
    def _openapi_swagger_ui(self):
        return render_template('swaggerui.html', title=self._app.name)


def create_api(app):
    api = MyAPI(app)
    from .auth import auth
    api.register_blueprint(auth)
