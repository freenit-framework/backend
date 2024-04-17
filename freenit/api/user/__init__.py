from freenit.models.user import User

if User.dbtype() == "sql":
    from .sql import UserListAPI, UserDetailAPI, ProfileDetailAPI
elif User.dbtype() == "ldap":
    from .ldap import UserListAPI, UserDetailAPI, ProfileDetailAPI
