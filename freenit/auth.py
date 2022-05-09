import jwt
import ormar
import ormar.exceptions
from fastapi import HTTPException, Request

from freenit.config import getConfig


async def decode(token):
    config = getConfig()
    User = config.get_user().User
    try:
        data = jwt.decode(token, config.secret, algorithms="HS256")
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


async def authorize(request: Request, cookie="access"):
    token = request.cookies.get(cookie)
    if not token:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return await decode(token)
