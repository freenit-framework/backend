try:
    from local_config import Config
except ImportError:
    from common_config import CommonConfig as Config


class DevConfig(Config):
    DEBUG = True
    JWT_COOKIE_SECURE = False
    SECURITY_SEND_REGISTER_EMAIL = False


class TestConfig(Config):
    TESTING = True
    JWT_COOKIE_SECURE = False
    DATABASE = 'sqlite:///test.db'


class ProdConfig(Config):
    pass


configs = {
    'development': DevConfig,
    'testing': TestConfig,
    'production': ProdConfig,
    'default': ProdConfig,
}
