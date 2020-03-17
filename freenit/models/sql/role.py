from flask_security import RoleMixin
from freenit.db import db
from peewee import CharField, ForeignKeyField, TextField

from .user import User

Model = db.Model


class Role(Model, RoleMixin):
    description = TextField(null=True)
    name = CharField(unique=True)


class UserRoles(Model):
    description = property(lambda self: self.role.description)
    name = property(lambda self: self.role.name)
    role = ForeignKeyField(Role, backref='users')
    user = ForeignKeyField(User, backref='roles')
