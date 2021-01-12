import os
import socket
from application import init

application = init('development')
hostname = socket.gethostname()
port = os.environ.get('FLASK_PORT', 5000)
prefix = application.config['OPENAPI_URL_PREFIX']
swagger_path = application.config['OPENAPI_SWAGGER_UI_PATH']
SWAGGER_PATH = f'{prefix}{swagger_path}'
SWAGGER_URL = f'http://{hostname}:{port}{SWAGGER_PATH}'
redoc_path = application.config['OPENAPI_REDOC_PATH']
REDOC_PATH = f'{prefix}{redoc_path}'
REDOC_URL = f'http://{hostname}:{port}{REDOC_PATH}'

print('*****************************************************')
print('')
print('   Swagger URL:', SWAGGER_URL)
print('   Redoc URL:', REDOC_URL)
print('')
print('*****************************************************')
