from freenit.models.role import Role
from freenit.models.user import User

if User.Meta.type == "ormar":
    from ormar.queryset.field_accessor import FieldAccessor

    RoleSafe = Role.get_pydantic(exclude={"users__password"})

    include_fields = set()
    for attr in dir(User):
        a = getattr(User, attr, None)
        if isinstance(a, FieldAccessor):
            include_fields.add(attr)

    UserSafe = User.get_pydantic(exclude={"password"}, include=include_fields)
elif User.Meta.type == "bonsai":
    from freenit.config import getConfig

    config = getConfig()
    auth = config.get_model("user")

    UserSafe = auth.UserSafe
    RoleSafe = Role
