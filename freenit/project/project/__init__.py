VERSION = '0.0.1'


def create_app(app):
    from .api import create_api
    create_api(app)
