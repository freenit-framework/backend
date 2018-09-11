import factory
from flask_security.utils import hash_password
from application.models.auth import User, Role


class UserFactory(factory.Factory):
    class Meta:
        model = User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    password = factory.LazyAttribute(lambda a: hash_password('Sekrit'))
    username = factory.Faker('name')


class AdminFactory(UserFactory):
    admin = True


class RoleFactory(factory.Factory):
    class Meta:
        model = Role

    name = factory.Faker('first_name')
