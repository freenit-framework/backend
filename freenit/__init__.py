from flask import Flask
from flask_collect import Collect
from flask_jwt_extended import JWTManager
from flask_security import PeeweeUserDatastore, Security

from .api import create_api
from .db import db


def create_app(config, app=None):
    if app is None:
        app = Flask(__name__)
        app.config.from_object(config)

    app.collect = Collect(app)
    db.init_app(app)
    app.db = db

    from .models.auth import User, Role, UserRoles
    app.user_datastore = PeeweeUserDatastore(
        app.db,
        User,
        Role,
        UserRoles,
    )
    app.security = Security(app, app.user_datastore)
    app.jwt = JWTManager(app)
    create_api(app)

    return app
