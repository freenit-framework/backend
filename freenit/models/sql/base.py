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
        data = fields.dict()
        for k in data:
            if data[k] is not None:
                result[k] = data[k]
        return await self.update(**result)


class OrmarUserMixin:
    id: int = ormar.Integer(primary_key=True)
    email: pydantic.EmailStr = ormar.Text(unique=True)
    password: str = ormar.Text()
    active: bool = ormar.Boolean(default=False)
    admin: bool = ormar.Boolean(default=False)


class OrmarRoleMixin:
    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.Text(unique=True)


ormar_config = ormar.OrmarConfig(
    database=config.database,
    metadata=config.metadata,
    engine=config.engine,
)


def generate_optional(Model):
    class OptionalModel(Model):
        pass

    for field_name in OptionalModel.model_fields:
        OptionalModel.model_fields[field_name].default = None

    return OptionalModel
