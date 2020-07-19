import sys
from importlib import import_module

import freenit.schemas.user
from flask import Flask, send_file
from flask_collect import Collect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_security import Security
from freenit.schemas.paging import PageOutSchema

from . import cli
from .api import create_api
from .utils import sendmail


def sqlinit(app):
    from flask_security import PeeweeUserDatastore
    from .db import db
    db.init_app(app)
    app.db = db
    try:
        User = import_module(f"{app.config['NAME']}.models.sql.user").User
    except ModuleNotFoundError:
        User = import_module(f"{app.config['NAME']}.models.user").User
    try:
        role_module = import_module(f"{app.config['NAME']}.models.role")
    except ModuleNotFoundError:
        role_module = import_module(f"{app.config['NAME']}.models.sql.role")
    Role = role_module.Role
    UserRoles = role_module.UserRoles
    app.user_datastore = PeeweeUserDatastore(
        app.db,
        User,
        Role,
        UserRoles,
    )
    app.security = Security(app, app.user_datastore)


def mongoinit(app):
    from flask_security import MongoEngineUserDatastore
    from flask_mongoengine import MongoEngine
    app.db = MongoEngine(app)
    try:
        User = import_module(f"{app.config['NAME']}.models.user").User
    except ModuleNotFoundError:
        User = import_module(f"{app.config['NAME']}.models.mongo.user").User
    try:
        Role = import_module(f"{app.config['NAME']}.models.role").Role
    except ModuleNotFoundError:
        Role = import_module(f"{app.config['NAME']}.models.mongo.role").Role
    app.user_datastore = MongoEngineUserDatastore(app.db, User, Role)
    app.security = Security(app, app.user_datastore)


def create_app(
    config,
    app=None,
    schemas={},
    dbtype='sql',
    name=__name__,
    **kwargs,
):
    if app is None:
        app = Flask(name, **kwargs)
        app.config.from_object(config)

    @app.route('/media/<path:path>')
    def send_media(path):
        fullPath = f"{app.config['MEDIA_PATH']}/{path}"
        if fullPath[0] != '/':
            fullPath = f"/{app.config['PROJECT_ROOT']}/{fullPath}"
        try:
            return send_file(fullPath)
        except FileNotFoundError:
            return 'No such file', 404

    app.sendmail = lambda message: sendmail(app.config, message)
    app.collect = Collect(app)
    app.dbtype = dbtype
    if dbtype in ['sql', 'all']:
        sqlinit(app)
    elif dbtype == 'mongo':
        mongoinit(app)
    user_module = schemas.get('user', None)
    if user_module is None:

        class UserSchema(freenit.schemas.user.BaseUserSchema):
            pass
    else:
        UserSchema = import_module(user_module).UserSchema
    setattr(freenit.schemas.user, 'UserSchema', UserSchema)
    PageOutSchema(UserSchema, sys.modules['freenit.schemas.user'])
    role_module = schemas.get('role', None)
    if role_module is None:

        class RoleSchema(freenit.schemas.role.BaseRoleSchema):
            pass
    else:
        RoleSchema = import_module(role_module).RoleSchema
    setattr(freenit.schemas.role, 'RoleSchema', RoleSchema)
    PageOutSchema(RoleSchema, sys.modules['freenit.schemas.role'])
    app.jwt = JWTManager(app)
    create_api(app)
    app.cors = CORS(app, supports_credentials=True)
    cli.register(app)

    return app
