from typing import List

from freenit.config import getConfig

config = getConfig()


class UserSafe(config.get_model("user").User.get_pydantic(exclude={"password"})):
    pass


class RoleSafe(config.get_model("role").BaseRole):
    users: List[UserSafe]
