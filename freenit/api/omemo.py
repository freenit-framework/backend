import json

from fastapi import Depends, HTTPException
from pydantic import BaseModel

from freenit.api.router import api
from freenit.config import getConfig
from freenit.encrypt import decrypt_for_user, encrypt_for_user
from freenit.models.user import User
from freenit.permissions import profile_perms

config = getConfig()
tags = ["omemo"]


class OmemoBundle(BaseModel):
    bundle: dict | None = None


def _user_id(user: User) -> str:
    return str(user.pk) if user.dbtype() == "sql" else user.dn


@api.get("/profile/omemo", tags=tags)
async def get_omemo_bundle(user: User = Depends(profile_perms)):
    encrypted = user.omemo_bundle
    if not encrypted:
        return {"bundle": None}
    try:
        decrypted = decrypt_for_user(encrypted, _user_id(user), config.secret)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to decrypt OMEMO bundle")
    return {"bundle": json.loads(decrypted)}


@api.post("/profile/omemo", tags=tags)
async def save_omemo_bundle(data: OmemoBundle, user: User = Depends(profile_perms)):
    if data.bundle is None:
        encrypted = None
    else:
        encrypted = encrypt_for_user(
            json.dumps(data.bundle), _user_id(user), config.secret
        )

    if user.dbtype() == "sql":
        user.omemo_bundle = encrypted
        await user.save(update_fields=["omemo_bundle"])
    else:
        await user.update(omemo_bundle=encrypted or "")

    return {"bundle": data.bundle}
