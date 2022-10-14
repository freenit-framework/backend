from math import ceil
from typing import Generic, List, TypeVar

from pydantic import Field, generics

T = TypeVar("T")


class Page(generics.GenericModel, Generic[T]):
    total: int = Field(0, description=("Total number of items in DB"))
    page: int = Field(0, description=("Current page"))
    perpage: int = Field(10, description=("Items per page"))
    data: List[T] = Field(..., description=("A list of the current page of results."))

    class Config:
        allow_population_by_field_name = True


async def paginate(query, page, perpage):
    total_items = await query.count()
    total = ceil(total_items / perpage)
    data = await query.paginate(page, perpage).all()
    return Page(data=data, page=page, total=total, perpage=perpage)
