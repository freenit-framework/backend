from importlib import import_module

from freenit.config import getConfig
from freenit.modules import MODULES, get_api_modules, resolve_modules

from .router import api

config = getConfig()

# Resolve the configured modules (including dependencies) and import their API
# modules. Each API module registers its routes on the shared `api` app as an
# import side-effect, preserving the existing decorator-based registration.
_module_names = resolve_modules(config.modules)
for _api_module in get_api_modules(config.modules):
    import_module(_api_module)


@api.get("/")
async def api_root():
    """Discovery endpoint: list active modules.

    The frontend uses this response to decide which features to expose.
    """
    return {
        "modules": sorted(_module_names),
        "meta": {
            name: {
                "dependencies": MODULES[name].dependencies,
            }
            for name in _module_names
        },
    }
