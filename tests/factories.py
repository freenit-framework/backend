from importlib import import_module

from flask_security.utils import hash_password

import factory
from name import app_name

user = import_module(f'{app_name}.models.sql.user')
role = import_module(f'{app_name}.models.sql.role')


class UserFactory(factory.Factory):
    class Meta:
        model = user.User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    password = factory.LazyAttribute(lambda a: hash_password('Sekrit'))
    username = factory.Faker('name')
    active = True


class AdminFactory(UserFactory):
    admin = True


class RoleFactory(factory.Factory):
    class Meta:
        model = role.Role

    name = factory.Faker('first_name')
