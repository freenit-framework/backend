from typing import Optional

import ormar
import pydantic

from ..config import getConfig

config = getConfig()


class AllOptional(pydantic.main.ModelMetaclass):
    def __new__(self, name, bases, namespaces, **kwargs):
        annotations = namespaces.get("__annotations__", {})
        for base in bases:
            annotations = {**annotations, **base.__annotations__}
        for field in annotations:
            if not field.startswith("__"):
                annotations[field] = Optional[annotations[field]]
        namespaces["__annotations__"] = annotations
        return super().__new__(self, name, bases, namespaces, **kwargs)


class MainMeta(ormar.ModelMeta):
    metadata = config.metadata
    database = config.database
