from fastapi_users.authentication import CookieAuthentication
from .config import getConfig

config = getConfig()
cookieAuthentication = CookieAuthentication(
    secret=config.secret,
    lifetime_seconds=3600,
    cookie_secure=config.cookie_secure,
)
authBackends = [cookieAuthentication]
