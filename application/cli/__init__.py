import click
from flask.cli import AppGroup
from peewee_migrate import Router

migration = AppGroup('migration')


def register(app):
    router = Router(app.db.database)

    @migration.command()
    def list():
        for migration in router.done:
            print(migration)

    @migration.command()
    @click.argument('name')
    def create(name):
        router.create(name, 'app.models')

    @migration.command()
    def run():
        router.run()

    app.cli.add_command(migration)
