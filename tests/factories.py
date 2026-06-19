import factory
from passlib.hash import pbkdf2_sha256

from freenit.config import getConfig
from freenit.models.project import (
    Board,
    Column,
    Project,
    ProjectGroup,
    ProjectGroupPermission,
    ProjectMember,
    Task,
)
from freenit.models.role import Role as RoleModel

config = getConfig()
auth = config.get_model("user")


class User(factory.Factory):
    class Meta:
        model = auth.User

    email = factory.Faker("email")
    password = pbkdf2_sha256.hash(f"{config.secret}Sekrit")
    active = True


class InactiveUser(User):
    active = False


class Role(factory.Factory):
    class Meta:
        model = RoleModel

    name = factory.Faker("pystr")


class ProjectFactory(factory.Factory):
    class Meta:
        model = Project

    name = factory.Faker("pystr")
    description = factory.Faker("sentence")
    created_by_id = None


class BoardFactory(factory.Factory):
    class Meta:
        model = Board

    name = factory.Faker("pystr")
    description = factory.Faker("sentence")
    project_id = None


class ColumnFactory(factory.Factory):
    class Meta:
        model = Column

    name = factory.Faker("pystr")
    position = factory.Faker("random_int")
    board_id = None


class TaskFactory(factory.Factory):
    class Meta:
        model = Task

    title = factory.Faker("pystr")
    description = factory.Faker("sentence")
    position = factory.Faker("random_int")
    column_id = None
    assignee_id = None


class ProjectGroupFactory(factory.Factory):
    class Meta:
        model = ProjectGroup

    name = factory.Faker("pystr")
    description = factory.Faker("sentence")
    project_id = None


class ProjectMemberFactory(factory.Factory):
    class Meta:
        model = ProjectMember

    group_id = None
    user_id = None


class ProjectGroupPermissionFactory(factory.Factory):
    class Meta:
        model = ProjectGroupPermission

    group_id = None
    permission = factory.Faker("pystr")
