def init(config_name, websocket=True):
    from importlib import import_module
    from freenit import create_app
    from config import configs
    from name import app_name

    app = import_module(f'{app_name}')
    config = configs[config_name]
    application = create_app(config)
    app.create_app(application, websocket)
    return application
