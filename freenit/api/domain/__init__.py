from freenit.models.user import User

if User.dbtype() == "ldap":
    from .ldap import DomainListAPI, DomainDetailAPI

