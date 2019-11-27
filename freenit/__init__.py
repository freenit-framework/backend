from flask import Flask, send_file
from flask_collect import Collect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_security import PeeweeUserDatastore, Security

from .api import create_api
from .db import db
from .utils import sendmail as sm


def create_app(config, app=None):
    if app is None:
        app = Flask(__name__)
        app.config.from_object(config)

    @app.route('/media/<path:path>')
    def send_media(path):
        fullPath = f"../{app.config['MEDIA_PATH']}/{path}"
        try:
            return send_file(fullPath)
        except FileNotFoundError:
            return 'No such file', 404

    app.sendmail = lambda to, message: sm(app.config, to, message)

    app.collect = Collect(app)
    db.init_app(app)
    app.db = db

    from .models.user import User
    from .models.role import Role, UserRoles
    app.user_datastore = PeeweeUserDatastore(
        app.db,
        User,
        Role,
        UserRoles,
    )
    app.security = Security(app, app.user_datastore)
    app.jwt = JWTManager(app)
    create_api(app)
    app.cors = CORS(app, supports_credentials=True)

    return app
