import peewee as pw

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
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
        active = pw.BooleanField(default=False)
        admin = pw.BooleanField(default=False)
        confirmed_at = pw.DateTimeField(null=True)
        email = pw.TextField(unique=True)
        password = pw.TextField()
        reset = pw.TextField(null=True)

        class Meta:
            table_name = "users"

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
            model=migrator.orm['users']
        )

        class Meta:
            table_name = "userroles"


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_model('userroles')
    migrator.remove_model('users')
    migrator.remove_model('role')
