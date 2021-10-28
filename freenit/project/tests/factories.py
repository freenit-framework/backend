import factory

from freenit.config import getConfig

config = getConfig()
auth = config.get_user()
UserModel = auth.UserModel


class UserFactory(factory.Factory):
    class Meta:
        model = UserModel

    id = factory.Faker("uuid4")
    is_active = True
    email = factory.Faker("email")
    hashed_password = "Sekrit"
