from freenit.config import getConfig

config = getConfig()
auth = config.get_model("role")


class Role(auth.Role):
    pass


class RoleOptional(auth.RoleOptional):
    pass
