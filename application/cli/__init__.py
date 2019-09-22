import click
from flask.cli import AppGroup
from flask_security.utils import hash_password
from peewee_migrate import Router

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
        router.create(name, 'application.models')

    @migration.command()
    def run():
        router.run()

    app.cli.add_command(migration)


def register_admin(app):
    @admin_group.command()
    def create():
        from ..models.auth import User
        admin, created = User.get_or_create(
            email='admin@example.com',
            password='Sekrit',
        )
        if created:
            admin.password = hash_password(admin.password)
            admin.admin = True
            admin.active = True
            admin.save()

    app.cli.add_command(admin_group)


def register(app):
    register_admin(app)
    register_migration(app)
