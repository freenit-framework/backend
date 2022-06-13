from freenit.config import getConfig

config = getConfig()
auth = config.get_group()
Group = auth.Group
GroupOptional = auth.GroupOptional
GroupUser = auth.GroupUser
GroupUserSafe = GroupUser.get_pydantic(exclude={"user__password"})
