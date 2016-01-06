import factory
from flask_security.utils import encrypt_password
import models


class UserFactory(factory.Factory):
    class Meta:
        model = models.auth.User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    password = encrypt_password('Sekrit')
    username = factory.Faker('name')


class AdminFactory(UserFactory):
    admin = True


class RoleFactory(factory.Factory):
    class Meta:
        model = models.auth.Role

    name = factory.Faker('first_name')
    admin = False
