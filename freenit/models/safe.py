from typing import List
from freenit.config import getConfig

config = getConfig()
auth = config.get_model("user")


if auth.User.dbtype() == 'sql':
    UserBase = auth.User.get_pydantic(exclude={"password"})
    RoleBase = config.get_model("role").BaseRole
elif auth.User.dbtype() == 'ldap':
    UserBase = auth.UserSafe
    RoleBase = config.get_model("role").Role


class UserSafe(UserBase):
    pass

class RoleSafe(RoleBase):
    users: List[str]
