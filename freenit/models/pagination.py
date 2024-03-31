from math import ceil
from typing import Generic, List, TypeVar

from fastapi import HTTPException
from pydantic import Field, BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    total: int = Field(0, description=("Total number of items in DB"))
    page: int = Field(0, description=("Current page"))
    pages: int = Field(0, description=("Total number of pages"))
    perpage: int = Field(10, description=("Items per page"))
    data: List[T] = Field(..., description=("List of results for the current page"))


async def paginate(query, page, perpage):
    total = await query.count()
    pages = ceil(total / perpage)
    if total > 0 and page > pages:
        raise HTTPException(status_code=404, detail="No such page")
    data = await query.paginate(page, perpage).all()
    return Page(data=data, page=page, perpage=perpage, pages=pages, total=total)
