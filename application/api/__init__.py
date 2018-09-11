from flask import Blueprint, render_template
from flask_restplus import Api, apidoc
from flask_jwt_extended.exceptions import (
    CSRFError,
    NoAuthorizationError,
)
from jwt import ExpiredSignatureError
from .namespaces import ns_auth, ns_me, ns_user


class ErrorFriendlyApi(Api):
    def error_router(self, original_handler, e):
        if type(e) in [
            CSRFError,
            ExpiredSignatureError,
            NoAuthorizationError,
        ]:
            return original_handler(e)
        else:
            return super(ErrorFriendlyApi, self).error_router(
                original_handler,
                e,
            )


def create_api(app):
    def swagger_ui():
        return render_template(
            'flask-restplus/swagger-ui.html',
            title=api.title,
            specs_url=api.specs_url
        )

    api_v0 = Blueprint('api', __name__, url_prefix='/api/v0')
    api = ErrorFriendlyApi(
        api_v0,
        version='0',
        title='API',
        description='API description',
        doc='/doc/',
        catch_all_404s=True,
        default='auth',
    )
    api._doc_view = swagger_ui
    api.add_namespace(ns_auth)
    api.add_namespace(ns_me)
    api.add_namespace(ns_user)
    app.api = api
    app.register_blueprint(api_v0)
    app.register_blueprint(apidoc.apidoc)
