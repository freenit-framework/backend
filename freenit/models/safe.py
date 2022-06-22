from ormar.queryset.field_accessor import FieldAccessor

from freenit.models.role import Role
from freenit.models.user import User

RoleSafe = Role.get_pydantic(exclude={"users__password"})

include_fields = set()
for attr in dir(User):
    a = getattr(User, attr, None)
    if isinstance(a, FieldAccessor):
        include_fields.add(attr)

UserSafe = User.get_pydantic(exclude={"password"}, include=include_fields)
