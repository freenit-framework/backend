import ormar
import pydantic

from freenit.config import getConfig

config = getConfig()


class OrmarBaseModel(ormar.Model):
    @classmethod
    def dbtype(cls):
        return "sql"

    async def patch(self, fields):
        result = {}
        data = fields.model_dump()
        for k in data:
            if data[k] is not None:
                result[k] = data[k]
        return await self.update(**result)


class OrmarUserMixin:
    id: int = ormar.Integer(primary_key=True)
    email: pydantic.EmailStr = ormar.Text(unique=True)
    password: str = ormar.Text()
    fullname: str = ormar.Text(nullable=True)
    active: bool = ormar.Boolean(default=False)
    admin: bool = ormar.Boolean(default=False)


class OrmarRoleMixin:
    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.Text(unique=True, index=True)


ormar_config = ormar.OrmarConfig(
    database=config.database,
    metadata=config.metadata,
    engine=config.engine,
)


def make_optional(OptionalModel):
    for field_name in OptionalModel.model_fields:
        OptionalModel.model_fields[field_name].default = None


class BaseRole(OrmarBaseModel, OrmarRoleMixin):
    ormar_config = ormar_config.copy(abstract=True)
