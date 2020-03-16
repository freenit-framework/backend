from freenit.api import register_endpoints


def create_api(app):
    register_endpoints(app, '/api/v0', [])
