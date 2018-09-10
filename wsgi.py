import os

from flask import Flask, render_template
from application import create_app, cli
from config import configs


config_name = os.getenv('FLASK_ENV') or 'default'
app = create_app(configs[config_name])
cli.register(app)


if __name__ == '__main__':
    app.run()
