from email.mime.text import MIMEText

import pydantic
from fastapi import Header, HTTPException, Request, Response

from freenit.api.router import api
from freenit.auth import authorize, decode, encode, encrypt
from freenit.config import getConfig
from freenit.mail import sendmail
from freenit.models.safe import UserSafe
from freenit.models.user import User

config = getConfig()


class LoginInput(pydantic.BaseModel):
    email: pydantic.EmailStr
    password: str


class TokenExpire(pydantic.BaseModel):
    access: int
    refresh: int


class LoginResponse(pydantic.BaseModel):
    user: UserSafe
    expire: TokenExpire


class Verification(pydantic.BaseModel):
    verification: str


@api.post("/auth/login", response_model=LoginResponse, tags=["auth"])
async def login(credentials: LoginInput, response: Response):
    user = await User.login(credentials)
    access = encode(user)
    refresh = encode(user)
    response.set_cookie(
        "access",
        access,
        httponly=True,
        secure=config.auth.secure,
    )
    response.set_cookie(
        "refresh",
        refresh,
        httponly=True,
        secure=config.auth.secure,
    )
    return {
        "user": user,
        "expire": {
            "access": config.auth.expire,
            "refresh": config.auth.refresh_expire,
        },
    }


@api.post("/auth/register", tags=["auth"])
async def register(credentials: LoginInput, host=Header(default="")):
    import ormar.exceptions

    try:
        user = await User.objects.get(email=credentials.email)
        raise HTTPException(status_code=409, detail="User already registered")
    except ormar.exceptions.NoMatch:
        pass
    user = User(
        email=credentials.email,
        password=encrypt(credentials.password),
        active=False,
    )
    await user.save()
    token = encode(user)
    print(token)
    mail = config.mail
    if mail is not None:
        message = mail.register_message.format(f"http://{host}/verify/{token}")
        msg = MIMEText(message, "plain", "utf-8")
        msg["From"] = mail.from_addr
        msg["Subject"] = mail.register_subject
        sendmail(user.email, msg)
    return {"status": True}


@api.post("/auth/verify", response_model=UserSafe, tags=["auth"])
async def verify(verification: Verification):
    user = await decode(verification.verification)
    await user.update(active=True)
    return user


@api.post("/auth/refresh", response_model=LoginResponse, tags=["auth"])
async def refresh(request: Request, response: Response):
    user = await authorize(request, cookie="refresh")
    access = encode(user)
    response.set_cookie("access", access, httponly=True, secure=config.auth.secure)
    return {
        "user": user,
        "expire": {
            "access": config.auth.expire,
            "refresh": config.auth.refresh_expire,
        },
    }
