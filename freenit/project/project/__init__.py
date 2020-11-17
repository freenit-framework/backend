from .api import create_api


def create_app(app):
    create_api(app)
