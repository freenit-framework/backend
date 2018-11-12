from application import create_app
from config import configs

config = configs['development']
app = create_app(config)
