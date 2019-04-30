from flask import render_template
from flask_rest_api import Api

from .auth import auth
from .user import user


class MyApi(Api):
    def _openapi_swagger_ui(self):
        return render_template('swaggerui.html', title=self._app.name)


def create_api(app):
    api = MyApi(app)
    api_prefix = '/api/v0'
    api.register_blueprint(
        auth,
        url_prefix='{}/{}'.format(
            api_prefix,
            auth.name,
        ),
    )
    api.register_blueprint(
        user,
        url_prefix='{}/{}'.format(
            api_prefix,
            user.name,
        ),
    )
