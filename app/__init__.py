from flask import Flask, Blueprint
from flask_collect import Collect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restplus import apidoc
from flask_security import Security, PeeweeUserDatastore
from flask_security.utils import verify_password
from werkzeug.security import safe_str_cmp
from .db import db


def create_app(config, app=None):
    class Result(object):
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    if app is None:
        app = Flask(__name__)
        app.config.from_object(config)

    debug = app.config.get('DEBUG', False)
    if debug:
        CORS(app)
    app.collect = Collect(app)
    db.init_app(app)
    app.db = db

    app.blueprint = Blueprint(
        'app',
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static/app',
    )
    app.register_blueprint(app.blueprint)

    from .api import api_v0, api
    app.api = api
    app.register_blueprint(api_v0)
    app.register_blueprint(apidoc.apidoc)

    from .models.auth import User, Role, UserRoles
    app.user_datastore = PeeweeUserDatastore(
        app.db,
        User,
        Role,
        UserRoles,
    )
    app.security = Security(app, app.user_datastore)

    app.jwt = JWTManager(app)

    from .api import auth, user

    return app
