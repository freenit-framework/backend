import factory
from freenit.models.user import UserModel
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserFactory(factory.Factory):
    class Meta:
        model = UserModel

    id = factory.Faker('uuid4')
    email = factory.Faker('email')
    hashed_password = pwd_context.hash('Sekrit')
    is_verified = True
    is_superuser = False
    is_active = True


class SuperUserFactory(UserFactory):
    is_superuser = True


class UnverfiedUserFactory(UserFactory):
    is_verified = False


class InactiveUserFactory(UserFactory):
    is_active = True
