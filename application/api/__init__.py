from flask import Blueprint, render_template
from flask_jwt_extended.exceptions import CSRFError, NoAuthorizationError
from flask_restplus import Api, apidoc
from jwt import ExpiredSignatureError

from .namespaces import namespaces
from .schemas import schemas


class ErrorFriendlyApi(Api):
    def error_router(self, original_handler, e):
        if type(e) in [
            CSRFError,
            ExpiredSignatureError,
            NoAuthorizationError,
        ]:
            return original_handler(e)
        else:
            return super(ErrorFriendlyApi,
                         self).error_router(
                             original_handler,
                             e,
                         )


def create_api(app):
    def swagger_ui():
        return render_template(
            'flask-restplus/swagger-ui.html',
            title=app.api.title,
            specs_url=app.api.specs_url
        )

    api_v0 = Blueprint('api_v0', __name__, url_prefix='/api/v0')
    app.api = ErrorFriendlyApi(
        api_v0,
        version='0',
        title='StartKit API',
        description='StartKit operations',
        doc='/doc/',
        catch_all_404s=True,
        default='auth',
    )
    app.api._doc_view = swagger_ui
    if len(namespaces) > 0:
        ns = namespaces[0]
        for schema in schemas:
            ns.add_model(schema.Meta.name, schema.fields())
        for ns in namespaces:
            app.api.add_namespace(ns)
    app.register_blueprint(api_v0)
    app.register_blueprint(apidoc.apidoc)
    from . import auth, me, user  # noqa: F401
