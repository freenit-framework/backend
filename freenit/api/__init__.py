from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.ext.marshmallow.common import resolve_schema_cls
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


def schema_name_resolver(schema):
    schema_cls = resolve_schema_cls(schema)
    name = schema_cls.__name__
    if name.endswith("Schema"):
        name = name[:-6] or name
    if schema.partial:
        if isinstance(schema.partial, list):
            for field in schema.partial:
                name += field.capitalize()
        name += 'Partial'
    return name


def create_api(app):
    from .auth import blueprint as auth
    from .me import blueprint as me
    from .role import blueprint as role
    from .user import blueprint as user

    marshmallow_plugin = MarshmallowPlugin(
        schema_name_resolver=schema_name_resolver
    )
    spec_kwargs = {
        'marshmallow_plugin': marshmallow_plugin,
    }
    app.api = MyApi(app, spec_kwargs=spec_kwargs)
    register_endpoints(
        app,
        '/api/v0',
        [
            auth,
            me,
            role,
            user,
        ],
    )
