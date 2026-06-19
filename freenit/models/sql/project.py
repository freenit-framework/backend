from __future__ import annotations

from datetime import datetime

import oxyde
import pydantic

from freenit.models.sql.base import OxydeBaseModel, User

NotFoundError = oxyde.NotFoundError
IntegrityError = oxyde.IntegrityError


class Project(OxydeBaseModel):
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
        table_name = "project"


class Board(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    project: Project | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    name: str = oxyde.Field()
    description: str | None = oxyde.Field(default=None)
    created_at: datetime | None = oxyde.Field(default=None)
    updated_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "board"
        unique_together = [("project_id", "name")]


class Column(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    board: Board | None = oxyde.Field(default=None, db_fk="id", db_on_delete="CASCADE")
    name: str = oxyde.Field()
    position: int = oxyde.Field(default=0)
    created_at: datetime | None = oxyde.Field(default=None)
    updated_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "board_column"
        unique_together = [("board_id", "name")]


class Task(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    column: Column | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    title: str = oxyde.Field()
    description: str | None = oxyde.Field(default=None)
    position: int = oxyde.Field(default=0)
    assignee: User | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="SET NULL"
    )
    parent: Task | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="SET NULL"
    )
    created_at: datetime | None = oxyde.Field(default=None)
    updated_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "task"


class ProjectOptional(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None


class BoardOptional(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None


class ColumnOptional(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str | None = None
    position: int | None = None


class TaskOptional(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    position: int | None = None
    column_id: int | None = None
    assignee_id: int | None = None
    parent_id: int | None = None


class ProjectGroup(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    project: Project | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    name: str = oxyde.Field()
    description: str | None = oxyde.Field(default=None)
    created_at: datetime | None = oxyde.Field(default=None)
    updated_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "project_group"
        unique_together = [("project_id", "name")]


class ProjectGroupOptional(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


class ProjectGroupPermission(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    group: ProjectGroup | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    permission: str = oxyde.Field()

    class Meta:
        is_table = True
        table_name = "project_group_permission"
        unique_together = [("group_id", "permission")]


class ProjectMember(OxydeBaseModel):
    id: int | None = oxyde.Field(default=None, db_pk=True)
    group: ProjectGroup | None = oxyde.Field(
        default=None, db_fk="id", db_on_delete="CASCADE"
    )
    user: User | None = oxyde.Field(default=None, db_fk="id", db_on_delete="CASCADE")
    created_at: datetime | None = oxyde.Field(default=None)

    class Meta:
        is_table = True
        table_name = "project_member"
        unique_together = [("group_id", "user_id")]


Project.model_rebuild()
Board.model_rebuild()
Column.model_rebuild()
Task.model_rebuild()
ProjectGroup.model_rebuild()
ProjectGroupPermission.model_rebuild()
ProjectMember.model_rebuild()
