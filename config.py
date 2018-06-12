from datetime import timedelta
import os


PROJECT_APP_PATH = os.path.dirname(os.path.abspath(__file__))


class Config:
    DEBUG = False
    SECURITY_PASSWORD_SALT = 'tilda'
    SECRET_KEY = 'iQfPvB6sZaNHqVFI5CJa9rM1xOEVHKIM0LwifT04yLsPlZhSSvaDuZXOgJFSpJVq'
    SECURITY_TRACKABLE = False
    JWT_EXPIRATION_DELTA = timedelta(days=7)
    DATABASE = 'sqlite:///database.db'

    @staticmethod
    def init_app(app):
        pass


class DevConfig(Config):
    DEBUG = True
    SECURITY_SEND_REGISTER_EMAIL = False


class TestConfig(Config):
    TESTING = True
    DATABASE = 'sqlite:///:memory:'


class ProdConfig(Config):
    pass


configs = {
    'development': DevConfig,
    'testing': TestConfig,
    'production': ProdConfig,
    'default': ProdConfig,
}
