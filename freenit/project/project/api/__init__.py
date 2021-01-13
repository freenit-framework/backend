def create_api(app):
    from freenit.api import register_endpoints

    api_version = app.config.get('API_VERSION', '')
    register_endpoints(app, f'/api/{api_version}', [])
