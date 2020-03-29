from freenit.models.TYPE.user import User as BaseUser


class User(BaseUser):
    class Meta:
        table_name = 'users'
