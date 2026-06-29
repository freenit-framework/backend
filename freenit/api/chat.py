from fastapi import Depends
from freenit.api.router import api
from freenit.config import getConfig
from freenit.permissions import profile_perms

config = getConfig()
tags = ["chat"]


@api.get("/chat/config", tags=tags)
async def chat_config(user=Depends(profile_perms)):
    return {
        "ws_url": config.xmpp.ws_url,
    }
