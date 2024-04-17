from freenit.models.role import Role

if Role.dbtype() == "sql":
    from .sql import RoleListAPI, RoleDetailAPI, RoleUserAPI
elif Role.dbtype() == "ldap":
    from .ldap import RoleListAPI, RoleDetailAPI, RoleUserAPI
