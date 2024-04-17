import ormar

from .base import OrmarBaseModel, ormar_config, generate_optional


class Theme(OrmarBaseModel):
    ormar_config = ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.Text(unique=True)
    bg_color: str = ormar.Text()
    bg_secondary_color: str = ormar.Text()
    color_primary: str = ormar.Text()
    color_lightGrey: str = ormar.Text()
    color_grey: str = ormar.Text()
    color_darkGrey: str = ormar.Text()
    color_error: str = ormar.Text()
    color_success: str = ormar.Text()
    grid_maxWidth: str = ormar.Text()
    grid_gutter: str = ormar.Text()
    font_size: str = ormar.Text()
    font_color: str = ormar.Text()
    font_family_sans: str = ormar.Text()
    font_family_mono: str = ormar.Text()


ThemeOptional = generate_optional(Theme)
