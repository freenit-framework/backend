from freenit.config import getConfig

config = getConfig()
theme = config.get_model("theme")
Theme = theme.Theme
ThemeOptional = theme.ThemeOptional
