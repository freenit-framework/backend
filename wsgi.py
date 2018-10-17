import os

from application import cli, create_app
from config import configs

config_name = os.getenv('FLASK_ENV') or 'default'
app = create_app(configs[config_name])
cli.register(app)

if __name__ == '__main__':
    app.run()
