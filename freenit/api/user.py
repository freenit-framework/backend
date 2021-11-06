from ..auth import fastapiUsers
from ..config import getConfig
from .router import api

config = getConfig()

api.include_router(fastapiUsers.get_users_router(), prefix="/users", tags=["users"])
