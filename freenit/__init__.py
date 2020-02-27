import sys
from importlib import import_module

import freenit.schemas.user
from flask import Flask, send_file
from flask_collect import Collect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_security import PeeweeUserDatastore, Security
from freenit.schemas.paging import PageOutSchema

from . import cli
from .api import create_api
from .db import db
from .utils import sendmail


def create_app(config, app=None, schemas={}):
    if app is None:
        app = Flask(__name__)
        app.config.from_object(config)

    @app.route('/media/<path:path>')
    def send_media(path):
        fullPath = f"{app.config['MEDIA_PATH']}/{path}"
        try:
            return send_file(fullPath)
        except FileNotFoundError:
            return 'No such file', 404

    app.sendmail = lambda to, message: sendmail(app.config, to, message)

    app.collect = Collect(app)
    db.init_app(app)
    app.db = db

    User = import_module(f"{config.NAME}.models.user").User
    role_module = import_module(f"{config.NAME}.models.role")
    Role = role_module.Role
    UserRoles = role_module.UserRoles

    app.user_datastore = PeeweeUserDatastore(
        app.db,
        User,
        Role,
        UserRoles,
    )

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

    app.security = Security(app, app.user_datastore)
    app.jwt = JWTManager(app)
    create_api(app)
    app.cors = CORS(app, supports_credentials=True)
    cli.register(app)

    return app
