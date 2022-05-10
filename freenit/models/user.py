from freenit.config import getConfig

config = getConfig()
auth = config.get_user()
User = auth.User
UserOptional = auth.UserOptional
