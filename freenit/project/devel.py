import os
import socket
from application import init

application = init('development')
hostname = socket.gethostname()
port = os.environ.get('FLASK_PORT', 5000)
prefix = application.config['OPENAPI_URL_PREFIX']
path = application.config['OPENAPI_SWAGGER_UI_PATH']
SWAGGER_PATH = f'{prefix}{path}'
SWAGGER_URL = f'http://{hostname}:{port}{SWAGGER_PATH}'

print('*****************************************************')
print('')
print('   Swagger URL:', SWAGGER_URL)
print('')
print('*****************************************************')
