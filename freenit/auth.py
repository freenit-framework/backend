import jwt
import ormar
import ormar.exceptions
from fastapi import HTTPException, Request
from passlib.hash import pbkdf2_sha256

from freenit.config import getConfig


async def decode(token):
    config = getConfig()
    User = config.get_user().User
    try:
        data = jwt.decode(token, config.secret, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=403, detail="Unauthorized")
    pk = data.get("pk", None)
    if pk is None:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        user = await User.objects.get(pk=pk)
        return user
    except ormar.exceptions.NoMatch:
        raise HTTPException(status_code=403, detail="Unauthorized")


def encode(user):
    config = getConfig()
    payload = {"pk": user.pk}
    return jwt.encode(payload, config.secret, algorithm="HS256")


async def authorize(request: Request, groups=[], allof=[], cookie="access"):
    token = request.cookies.get(cookie)
    if not token:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user = await decode(token)
    if not user.active:
        raise HTTPException(status_code=403, detail="Permission denied")
    if user.admin:
        return user
    if user.groupusers is None:
        if len(groups) > 0 or len(allof) > 0:
            raise HTTPException(status_code=403, detail="Permission denied")
    else:
        found = False
        for groupuser in user.groupusers:
            if groupuser.group.name in groups:
                found = True
                break
        if not found:
            raise HTTPException(status_code=403, detail="Permission denied")
        for groupuser in user.groupusers:
            if groupuser.group.name not in allof:
                raise HTTPException(status_code=403, detail="Permission denied")
    return user


def verify(password, encpassword):
    config = getConfig()
    return pbkdf2_sha256.verify(f"{config.secret}{password}", encpassword)


def encrypt(password):
    config = getConfig()
    return pbkdf2_sha256.hash(f"{config.secret}{password}")


def permissions(groups=[], allof=[]):
    async def handler(request: Request):
        user = await authorize(request, groups, allof)
        return user

    return handler
