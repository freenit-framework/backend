# flake8: noqa
"""Peewee migrations -- 001_initial.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['model_name']            # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.python(func, *args, **kwargs)        # Run python code
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.drop_index(model, *col_names)
    > migrator.add_not_null(model, *field_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)

"""

import peewee as pw

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""

    @migrator.create_model
    class Role(pw.Model):
        id = pw.AutoField()
        description = pw.TextField(null=True)
        name = pw.CharField(max_length=255, unique=True)

        class Meta:
            table_name = "role"

    @migrator.create_model
    class User(pw.Model):
        id = pw.AutoField()
        active = pw.BooleanField(constraints=[SQL("DEFAULT True")])
        admin = pw.BooleanField(constraints=[SQL("DEFAULT False")])
        confirmed_at = pw.DateTimeField(null=True)
        email = pw.TextField()
        password = pw.TextField()

        class Meta:
            table_name = "user"

    @migrator.create_model
    class UserRoles(pw.Model):
        id = pw.AutoField()
        role = pw.ForeignKeyField(
            backref='users',
            column_name='role_id',
            field='id',
            model=migrator.orm['role']
        )
        user = pw.ForeignKeyField(
            backref='roles',
            column_name='user_id',
            field='id',
            model=migrator.orm['user']
        )

        class Meta:
            table_name = "userroles"


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""

    migrator.remove_model('userroles')

    migrator.remove_model('user')

    migrator.remove_model('role')
