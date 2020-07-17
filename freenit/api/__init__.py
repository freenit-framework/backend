from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.ext.marshmallow.common import resolve_schema_cls
from flask import render_template
from flask_smorest import Api


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
    if getattr(schema, 'partial', None):
        if isinstance(schema.partial, list):
            for field in schema.partial:
                name += field.capitalize()
        name += 'Partial'
    if getattr(schema, 'only', None):
        for field in schema.only:
            name += field.capitalize()
        name += 'Only'
    if getattr(schema, 'exclude', None):
        for field in schema.exclude:
            name += field.capitalize()
        name += 'Exclude'
    return name


def create_api(app):
    from .profile import blueprint as profile
    from .role import blueprint as role
    from .user import blueprint as user

    marshmallow_plugin = MarshmallowPlugin(
        schema_name_resolver=schema_name_resolver
    )
    spec_kwargs = {
        'marshmallow_plugin': marshmallow_plugin,
    }
    app.api = MyApi(app, spec_kwargs=spec_kwargs)
    if app.config.get('USE_AUTH', True):
        from .auth import blueprint as auth
        register_endpoints(app, '/api/v0', [auth])
    register_endpoints(
        app,
        '/api/v0',
        [
            profile,
            role,
            user,
        ],
    )
