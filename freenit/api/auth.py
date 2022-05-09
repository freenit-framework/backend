import jwt
import ormar
import ormar.exceptions
import pydantic
from fastapi import HTTPException, Request, Response

from freenit.api.router import api
from freenit.auth import authorize, decode
from freenit.config import getConfig

config = getConfig()
User = config.get_user().User
tags = ["auth"]


class LoginInput(pydantic.BaseModel):
    email: pydantic.EmailStr
    password: str


class TokenExpire(pydantic.BaseModel):
    access: int
    refresh: int


UserResponse = User.get_pydantic(exclude={"password": ...})


class LoginResponse(pydantic.BaseModel):
    user: UserResponse
    expire: TokenExpire


class Verification(pydantic.BaseModel):
    verification: str


@api.post("/auth/login", response_model=LoginResponse, tags=tags)
async def login(credentials: LoginInput, response: Response):
    try:
        user = await User.objects.get(email=credentials.email)
        valid = user.check(credentials.password)
        if valid:
            access = jwt.encode({"pk": user.pk}, config.secret, algorithm="HS256")
            refresh = jwt.encode({"pk": user.pk}, config.secret, algorithm="HS256")
            response.set_cookie(
                "access", access, httponly=True, secure=config.auth.secure
            )
            response.set_cookie(
                "refresh", refresh, httponly=True, secure=config.auth.secure
            )
            return {
                "user": user.dict(exclude={"password"}),
                "expire": {
                    "access": config.auth.expire,
                    "refresh": config.auth.refresh_expire,
                },
            }
    except ormar.exceptions.NoMatch:
        pass
    raise HTTPException(status_code=403, detail="Failed to login")


@api.post("/auth/register", response_model=Verification, tags=tags)
async def register(credentials: LoginInput):
    user = User(email=credentials.email, password=credentials.password, active=False)
    await user.save()
    verification = jwt.encode({"pk": user.pk}, config.secret, algorithm="HS256")
    return {"verification": verification}


@api.post("/auth/verify", response_model=UserResponse, tags=tags)
async def verify(verification: Verification):
    user = await decode(verification.verification)
    await user.update(active=True)
    return user


@api.post("/auth/refresh", response_model=LoginResponse, tags=tags)
async def refresh(request: Request, response: Response):
    user = await authorize(request, "refresh")
    access = jwt.encode({"pk": user.pk}, config.secret, algorithm="HS256")
    response.set_cookie("access", access, httponly=True, secure=config.auth.secure)
    return {
        "user": user.dict(exclude={"password"}),
        "expire": {
            "access": config.auth.expire,
            "refresh": config.auth.refresh_expire,
        },
    }
