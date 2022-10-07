from freenit.config import getConfig

config = getConfig()
auth = config.get_model("role")
Role = auth.Role
RoleOptional = auth.RoleOptional
