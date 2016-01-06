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

import datetime as dt
import peewee as pw

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""

    @migrator.create_model
    class Role(pw.Model):
        description = pw.TextField(null=True)
        name = pw.CharField(max_length=255, unique=True)

        class Meta:
            db_table = "role"

    @migrator.create_model
    class User(pw.Model):
        active = pw.BooleanField(default=True)
        admin = pw.BooleanField(default=False)
        confirmed_at = pw.DateTimeField(null=True)
        email = pw.TextField()
        password = pw.TextField()

        class Meta:
            db_table = "user"

    @migrator.create_model
    class UserRoles(pw.Model):
        role = pw.ForeignKeyField(db_column='role_id', rel_model=migrator.orm['role'], related_name='users', to_field='id')
        user = pw.ForeignKeyField(db_column='user_id', rel_model=migrator.orm['user'], related_name='roles', to_field='id')

        class Meta:
            db_table = "userroles"



def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""

    migrator.remove_model('userroles')

    migrator.remove_model('user')

    migrator.remove_model('role')
