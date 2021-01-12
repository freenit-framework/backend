def init(config_name):
    from freenit import create_app
    from config import configs

    config = configs[config_name]
    application = create_app(config)
    return application
