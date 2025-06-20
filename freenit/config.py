import os

try:
    from .local_config import DevConfig
except ModuleNotFoundError:
    from .base_config import DevConfig
except ImportError:
    from .base_config import DevConfig

try:
    from .local_config import TestConfig
except ModuleNotFoundError:
    from .base_config import TestConfig
except ImportError:
    from .base_config import TestConfig

try:
    from .local_config import ProdConfig
except ModuleNotFoundError:
    from .base_config import ProdConfig
except ImportError:
    from .base_config import ProdConfig

configs = {}
configs[DevConfig.envname()] = DevConfig()
configs[TestConfig.envname()] = TestConfig()
configs[ProdConfig.envname()] = ProdConfig()


def getConfig():
    config_name = os.getenv("FREENIT_ENV", "prod")
    return configs.get(config_name, configs["prod"])
