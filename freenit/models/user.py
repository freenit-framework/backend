from freenit.config import getConfig

config = getConfig()
auth = config.get_model("user")
User = auth.User
UserOptional = auth.UserOptionalPydantic
