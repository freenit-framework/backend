from freenit.models.role import Role
from freenit.models.user import User

if User.dbtype() == "sql":
    RoleSafe = Role.get_pydantic(exclude={"users__password"})
    UserSafe = User.get_pydantic(exclude={"password"})
elif User.dbtype() == "ldap":
    from freenit.config import getConfig
    config = getConfig()
    auth = config.get_model("user")
    UserSafe = auth.UserSafe
    RoleSafe = Role
