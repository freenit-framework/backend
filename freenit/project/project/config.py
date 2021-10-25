from freenit.config import configs

try:
    from .local_config import DevConfig
except ImportError:
    from .base_config import DevConfig

try:
    from .local_config import TestConfig
except ImportError:
    from .base_config import TestConfig

try:
    from .local_config import ProdConfig
except ImportError:
    from .base_config import ProdConfig


configs[DevConfig.envname()] = DevConfig()
configs[TestConfig.envname()] = TestConfig()
configs[ProdConfig.envname()] = ProdConfig()
