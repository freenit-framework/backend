from common_config import TestConfig as TestConfigBase

REDIS_HOST = 'localhost'


class TestConfig(TestConfigBase):
    MONGODB_SETTINGS = {
        'host': 'localhost',
    }
    REDIS_HOST = REDIS_HOST
    CELERY_BROKER_URL = 'redis://{}:6379'.format(REDIS_HOST)
    CELERY_RESULT_BACKEND = 'redis://{}:6379'.format(REDIS_HOST)
