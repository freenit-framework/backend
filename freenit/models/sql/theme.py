from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .base import Theme


class ThemeOptional(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    bg_color: str | None = None
    bg_secondary_color: str | None = None
    color_primary: str | None = None
    color_lightGrey: str | None = None
    color_grey: str | None = None
    color_darkGrey: str | None = None
    color_error: str | None = None
    color_success: str | None = None
    grid_maxWidth: str | None = None
    grid_gutter: str | None = None
    font_size: str | None = None
    font_color: str | None = None
    font_family_sans: str | None = None
    font_family_mono: str | None = None
