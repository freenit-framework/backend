from freenit.config import getConfig

config = getConfig()
auth = config.get_model("user")


class User(auth.User):
    pass


class UserOptional(auth.UserOptional):
    pass
