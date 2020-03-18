from flask_security import RoleMixin

from flask_mongoengine import Document
from mongoengine.fields import StringField


class Role(Document, RoleMixin):
    name = StringField(max_length=255)
    description = StringField(max_length=255)

    def __repr__(self):
        return '<Role %r>' % self.name
