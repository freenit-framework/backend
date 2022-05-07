import ormar

from .base import UserMixin


class OrmarUserMixin(UserMixin):
    email: str = ormar.Text(unique=True)
    password: str = ormar.Text()
