import ormar
import ormar.exceptions
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.config import getConfig
from freenit.decorators import description
from freenit.models.pagination import Page, paginate
from freenit.models.theme import Theme, ThemeOptional
from freenit.models.user import User
from freenit.permissions import theme_perms

tags = ["theme"]
config = getConfig()
default_theme = {
    "name": config.theme_name,
    "bg_color": "#ffffff",
    "bg_secondary_color": "#f3f3f6",
    "color_primary": "#14854F",
    "color_lightGrey": "#d2d6dd",
    "color_grey": "#747681",
    "color_darkGrey": "#3f4144",
    "color_error": "#d43939",
    "color_success": "#28bd14",
    "grid_maxWidth": "120rem",
    "grid_gutter": "2rem",
    "font_size": "1.6rem",
    "font_color": "#333333",
    "font_family_sans": "",
    "font_family_mono": "monaco, Consolas, Lucida Console, monospace",
}


@route("/themes", tags=tags)
class ThemeListAPI:
    @staticmethod
    @description("Get themes")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
    ) -> Page[Theme]:
        themes = Theme.objects
        return await paginate(themes, page, perpage)

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


@route("/theme/active", tags=tags)
class ThemeActiveAPI:
    @staticmethod
    async def get() -> Theme:
        theme, _ = await Theme.objects.get_or_create(**default_theme)
        return theme
