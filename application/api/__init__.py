from flask import render_template
from flask_rest_api import Api


class MyApi(Api):
    def _openapi_swagger_ui(self):
        return render_template('swaggerui.html', title=self._app.name)


def register_endpoints(app, api_prefix, blueprints):
    for blueprint in blueprints:
        app.api.register_blueprint(
            blueprint,
            url_prefix='{}/{}'.format(
                api_prefix,
                blueprint.name,
            ),
        )


def create_api(app):
    from .auth import blueprint as auth
    from .user import blueprint as user

    app.api = MyApi(app)
    register_endpoints(
        app,
        '/api/v0',
        [
            auth,
            user,
        ],
    )
