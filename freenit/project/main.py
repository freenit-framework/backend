from NAME.app import app
from freenit.config import getConfig


config = getConfig()
print()
print(f"    http://{config.hostname}:{config.port}/api/v1/docs")
print(f"    http://{config.hostname}:{config.port}/api/v1/redoc")
print()
