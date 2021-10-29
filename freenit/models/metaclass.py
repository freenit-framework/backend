from typing import Optional

import ormar


class AllOptional(ormar.models.metaclass.ModelMetaclass):
    def __new__(cls, name, bases, namespaces, **kwargs):
        annotations = namespaces.get("__annotations__", {})
        for base in bases:
            annotations = {**annotations, **base.__annotations__}
        for field in annotations:
            if not field.startswith("__"):
                f = annotations[field]
                annotations[field] = Optional[f]
        namespaces["__annotations__"] = annotations
        return super().__new__(cls, name, bases, namespaces, **kwargs)
