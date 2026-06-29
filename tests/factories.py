import factory
from passlib.hash import pbkdf2_sha256

from freenit.config import getConfig
from freenit.models.blog import BlogPost, Tag
from freenit.models.lms import (
    Course,
    CourseGroup,
    CourseGroupPermission,
    CourseMember,
    Lecture,
)
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


class CourseFactory(factory.Factory):
    class Meta:
        model = Course

    name = factory.Faker("pystr")
    description = factory.Faker("sentence")
    created_by_id = None


class LectureFactory(factory.Factory):
    class Meta:
        model = Lecture

    title = factory.Faker("pystr")
    content = factory.Faker("sentence")
    position = factory.Faker("random_int")
    state = "draft"
    course_id = None


class CourseGroupFactory(factory.Factory):
    class Meta:
        model = CourseGroup

    name = factory.Faker("pystr")
    description = factory.Faker("sentence")
    course_id = None


class CourseMemberFactory(factory.Factory):
    class Meta:
        model = CourseMember

    group_id = None
    user_id = None


class CourseGroupPermissionFactory(factory.Factory):
    class Meta:
        model = CourseGroupPermission

    group_id = None
    permission = "edit"


class TagFactory(factory.Factory):
    class Meta:
        model = Tag

    name = factory.Faker("pystr")


class BlogPostFactory(factory.Factory):
    class Meta:
        model = BlogPost

    title = factory.Faker("sentence")
    slug = factory.Faker("pystr")
    content = factory.Faker("paragraph")
    date = factory.Faker("date_time")
    published = True
    author_id = None
