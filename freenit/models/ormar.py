import ormar
import pydantic


class OrmarUserMixin:
    id: int = ormar.Integer(primary_key=True)
    email: pydantic.EmailStr = ormar.Text(unique=True)
    password: str = ormar.Text()
    active: bool = ormar.Boolean(default=False)
