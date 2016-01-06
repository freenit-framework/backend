#!/usr/bin/env python
import os

from flask import Flask, render_template
from flask_script import Manager, Server

from app import create_app
from app.script import CreateAdminCommand
from config import configs


config_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(configs[config_name])

app.manager = Manager(app)
app.manager.add_command('create_admin', CreateAdminCommand)
app.manager.add_command('db', app.db.manager)
app.manager.add_command('runserver', Server(
        host='0.0.0.0',
        use_reloader=True,
        use_debugger=True,
    )
)

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.manager.run()
