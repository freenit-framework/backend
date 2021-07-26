import factory
from freenit.models.user import UserModel


class UserFactory(factory.Factory):
    class Meta:
        model = UserModel

    id = factory.Faker('uuid4')
    is_active = True
    email = factory.Faker('email')
    hashed_password = 'Sekrit'
