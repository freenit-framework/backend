from importlib import import_module

from config import configs
from name import app_name

application = import_module(f'{app_name}')
config = configs['development']
app = application.create_app(config)
