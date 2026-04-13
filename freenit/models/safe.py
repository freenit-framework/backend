from typing import List
from pydantic import BaseModel, ConfigDict, EmailStr
from freenit.config import getConfig

config = getConfig()
auth = config.get_model("user")


if auth.User.dbtype() == "sql":
    class UserBase(BaseModel):
        model_config = ConfigDict(from_attributes=True)

        id: int | None = None
        email: EmailStr
        fullname: str | None = None
        active: bool = False
        admin: bool = False

    class RoleBase(BaseModel):
        model_config = ConfigDict(from_attributes=True)

        id: int | None = None
        name: str
elif auth.User.dbtype() == "ldap":
    UserBase = auth.UserSafe
    RoleBase = config.get_model("role").Role


class UserSafe(UserBase):
    pass


class RoleSafe(RoleBase):
    users: List[str]
