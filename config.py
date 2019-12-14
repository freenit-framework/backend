try:
    from local_config import DevConfig
except ImportError:
    from common_config import DevConfig

try:
    from local_config import TestConfig
except ImportError:
    from common_config import TestConfig

try:
    from local_config import ProdConfig
except ImportError:
    from common_config import ProdConfig

configs = {
    'development': DevConfig,
    'testing': TestConfig,
    'production': ProdConfig,
    'default': ProdConfig,
}
