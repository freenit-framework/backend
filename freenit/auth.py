import jwt
from fastapi import HTTPException, Request
from passlib.hash import pbkdf2_sha256

from freenit.config import getConfig


async def decode(token):
    config = getConfig()
    User = config.get_model("user").User
    try:
        data = jwt.decode(token, config.secret, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=403, detail="Unauthorized")
    pk = data.get("pk", None)
    if pk is None:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if User.dbtype() == "sql":
        import ormar
        import ormar.exceptions

        try:
            user = await User.objects.select_related("roles").get(pk=pk)
            return user
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=403, detail="Unauthorized")
    elif User.dbtype() == "ldap":
        user = await User.get(pk)
        return user
    raise HTTPException(status_code=409, detail="Unknown user type")


def encode(user):
    config = getConfig()
    payload = {}
    if user.dbtype() == "sql":
        payload = {"pk": user.pk, "type": "sql"}
    elif user.dbtype() == "ldap":
        payload = {"pk": user.dn, "type": "ldap"}
    return jwt.encode(payload, config.secret, algorithm="HS256")


async def authorize(request: Request, roles=[], allof=[], cookie="access"):
    token = request.cookies.get(cookie)
    if not token:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user = await decode(token)
    if user.dbtype() == "sql":
        if not user.active:
            raise HTTPException(status_code=403, detail="Permission denied")
        if user.admin:
            return user
        if len(user.roles) == 0:
            if len(roles) > 0 or len(allof) > 0:
                raise HTTPException(status_code=403, detail="Permission denied")
        else:
            if len(roles) > 0:
                found = False
                for role in user.roles:
                    if role.name in roles:
                        found = True
                        break
                if not found:
                    raise HTTPException(status_code=403, detail="Permission denied")
            if len(allof) > 0:
                for role in user.roles:
                    if role.name not in allof:
                        raise HTTPException(status_code=403, detail="Permission denied")
        return user
    elif user.dbtype() == "ldap":
        from freenit.models.ldap.base import get_client, class2filter
        from bonsai import LDAPSearchScope, errors

        config = getConfig()
        _, domain = user.email.split("@")
        classes = class2filter(config.ldap.groupClasses)
        dn = f"{config.ldap.domainDN.format(domain)},{config.ldap.roleBase}"
        client = get_client()
        async with client.connect(is_async=True) as conn:
            try:
                res = await conn.search(
                    dn,
                    LDAPSearchScope.SUB,
                    f"(&{classes}(memberUid={user.uidNumber}))",
                )
            except errors.AuthenticationError:
                raise HTTPException(status_code=403, detail="Failed to login")
        user.groups = [g["gidNumber"][0] for g in res]
    return user


def verify(password, encpassword):
    config = getConfig()
    return pbkdf2_sha256.verify(f"{config.secret}{password}", encpassword)


def encrypt(password):
    config = getConfig()
    return pbkdf2_sha256.hash(f"{config.secret}{password}")


def permissions(roles=[], allof=[]):
    async def handler(request: Request):
        user = await authorize(request, roles, allof)
        return user

    return handler
