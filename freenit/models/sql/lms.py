from __future__ import annotations

from datetime import datetime
from enum import StrEnum

import oxyde
import pydantic

from freenit.models.sql.base import OxydeBaseModel, User

NotFoundError = oxyde.NotFoundError
IntegrityError = oxyde.IntegrityError


class LectureState(StrEnum):
    DRAFT = "draft"
    PUBLISHED_PUBLIC = "published_public"
    PUBLISHED_PRIVATE = "published_private"


class Course(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    name: str = oxyde.Field(db_unique=True)
    description: str | None = oxyde.Field(default=None)
    created_by: User | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="SET NULL"
    )
    created_at: datetime | None = oxyde.Field(default=None)
    updated_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "course"


class Lecture(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    course: Course | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    title: str = oxyde.Field()
    content: str | None = oxyde.Field(default=None)
    position: int = oxyde.Field(default=0)
    state: LectureState = oxyde.Field(default=LectureState.DRAFT)
    created_at: datetime | None = oxyde.Field(default=None)
    updated_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "lecture"
        unique_together = [("course_id", "title")]


class CourseOptional(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None


class LectureOptional(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    title: str | None = None
    content: str | None = None
    position: int | None = None
    state: LectureState | None = None


class CourseGroup(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    course: Course | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    name: str = oxyde.Field()
    description: str | None = oxyde.Field(default=None)
    created_at: datetime | None = oxyde.Field(default=None)
    updated_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "course_group"
        unique_together = [("course_id", "name")]


class CourseGroupOptional(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


class CourseGroupPermission(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    group: CourseGroup | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    permission: str = oxyde.Field()

    class Meta:
        is_table = True
        table_name = "course_group_permission"
        unique_together = [("group_id", "permission")]


class CourseMember(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    group: CourseGroup | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    user: User | None = oxyde.Field(default=None, db_fk="id", db_on_delete="CASCADE")
    created_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "course_member"
        unique_together = [("group_id", "user_id")]


Course.model_rebuild()
Lecture.model_rebuild()
CourseGroup.model_rebuild()
CourseGroupPermission.model_rebuild()
CourseMember.model_rebuild()
