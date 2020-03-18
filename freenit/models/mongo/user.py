from flask_security import UserMixin

from flask_mongoengine import Document
from mongoengine.fields import (
    BooleanField,
    EmailField,
    ListField,
    ReferenceField,
    StringField
)

from .role import Role


class User(Document, UserMixin):
    active = BooleanField(default=False)
    admin = BooleanField()
    email = EmailField(unique=True)
    first_name = StringField(max_length=255)
    last_name = StringField(max_length=255)
    password = StringField(max_length=255)
    roles = ListField(ReferenceField(Role), default=[])

    def __repr__(self):
        return '<User %r>' % self.email
