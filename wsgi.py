import os
import socket

from config import configs
from freenit import create_app

config_name = os.getenv('FLASK_ENV') or 'default'
config = configs[config_name]
app = create_app(config)
hostname = socket.gethostname()
port = os.environ.get('FLASK_PORT', 5000)
REDOC_PATH = f'{config.OPENAPI_URL_PREFIX}{config.OPENAPI_REDOC_PATH}'
REDOC_URL = f'http://{hostname}:{port}{REDOC_PATH}'
SWAGGER_PATH = f'{config.OPENAPI_URL_PREFIX}{config.OPENAPI_SWAGGER_UI_PATH}'
SWAGGER_URL = f'http://{hostname}:{port}{SWAGGER_PATH}'
print(' * ReDoc URL:', REDOC_URL)
print(' * Swagger URL:', SWAGGER_URL)

if __name__ == '__main__':
    app.run()
