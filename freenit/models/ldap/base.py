from typing import Generic, TypeVar

from pydantic import EmailStr, Field, generics

T = TypeVar("T")


class LDAPBaseModel(generics.GenericModel, Generic[T]):
    class Meta:
        type = "bonsai"

    dn: str = Field("", description=("Distinguished name"))


class LDAPUserMixin:
    uid: str = Field("", description=("User ID"))
    email: EmailStr = Field("", description=("Email"))
    cn: str = Field("", description=("Common name"))
    sn: str = Field("", description=("Surname"))
