from importlib import import_module

import click
from flask.cli import AppGroup
from flask_security.utils import hash_password
from name import app_name
from peewee_migrate import Router

auth = import_module(f'{app_name}.models.auth')

migration = AppGroup('migration', short_help='Migration operations')
admin_group = AppGroup('admin', short_help='Manage admin users')


def register_migration(app):
    router = Router(app.db.database)

    @migration.command()
    def list():
        for migration in router.done:
            print(migration)

    @migration.command()
    @click.argument('name')
    def create(name):
        router.create(name, f'{app_name}.models')

    @migration.command()
    def run():
        router.run()

    app.cli.add_command(migration)


def register_admin(app):
    @admin_group.command()
    def create():
        try:
            auth.User.get(email='admin@example.com')
        except auth.User.DoesNotExist:
            admin = auth.User(
                email='admin@example.com',
                admin=True,
                active=True,
                password=hash_password('Sekrit'),
            )
            admin.save()

    app.cli.add_command(admin_group)


def register(app):
    register_admin(app)
    register_migration(app)
