from typing import List

import ormar
import ormar.exceptions
from fastapi import Depends, HTTPException

from freenit.api.router import route
from freenit.decorators import description
from freenit.models.theme import Theme, ThemeOptional
from freenit.models.user import User
from freenit.permissions import theme_perms

tags = ["theme"]


@route("/themes", tags=tags)
class ThemeListAPI:
    @staticmethod
    @description("Get themes")
    async def get() -> List[Theme]:
        return await Theme.objects.select_all().exclude_fields(["password"]).all()

    @staticmethod
    async def post(theme: Theme, _: User = Depends(theme_perms)) -> Theme:
        await theme.save()
        return theme


@route("/themes/{name}", tags=tags)
class ThemeDetailAPI:
    @staticmethod
    async def get(name: str) -> Theme:
        try:
            theme = await Theme.objects.select_all().get(name=name)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such theme")
        return theme

    @staticmethod
    async def patch(
        name: str, theme_data: ThemeOptional, _: User = Depends(theme_perms)
    ) -> Theme:
        try:
            theme = await Theme.objects.select_all().get(name=name)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such theme")
        await theme.patch(theme_data)
        return theme

    @staticmethod
    async def delete(name: str, _: User = Depends(theme_perms)) -> Theme:
        try:
            theme = await Theme.objects.select_all().get(name=name)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such theme")
        await theme.delete()
        return theme
