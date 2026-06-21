from datetime import datetime

import oxyde
import pydantic
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.decorators import description
from freenit.models.pagination import Page, paginate
from freenit.models.project import (
    Board,
    BoardOptional,
    Column,
    ColumnOptional,
    Project,
    ProjectGroup,
    ProjectGroupOptional,
    ProjectGroupPermission,
    ProjectMember,
    ProjectOptional,
    Task,
    TaskOptional,
)
from freenit.models.user import User
from freenit.permissions import project_perms

tags = ["project"]


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class ProjectCreate(pydantic.BaseModel):
    name: str
    description: str | None = None


class ProjectResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    created_by_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BoardCreate(pydantic.BaseModel):
    name: str
    description: str | None = None


class BoardResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ColumnCreate(pydantic.BaseModel):
    name: str
    position: int | None = None


class ColumnResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    board_id: int
    name: str
    position: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TaskCreate(pydantic.BaseModel):
    title: str
    description: str | None = None
    position: int | None = None
    assignee_id: int | None = None
    parent_id: int | None = None


class TaskResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    column_id: int
    title: str
    description: str | None = None
    position: int
    assignee_id: int | None = None
    parent_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TaskDetailResponse(TaskResponse):
    children: list[TaskResponse] = []
    parent: TaskResponse | None = None


class ProjectGroupCreate(pydantic.BaseModel):
    name: str
    description: str | None = None
    permissions: list[str] = []


class ProjectGroupResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    description: str | None = None
    permissions: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectGroupMemberCreate(pydantic.BaseModel):
    user_id: int


class ProjectGroupMemberResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    group_id: int
    user_id: int
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_project(id: int) -> Project:
    try:
        return await Project.objects.get(id=id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such project")


async def _get_board(id: int) -> Board:
    try:
        return await Board.objects.get(id=id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such board")


async def _get_column(id: int) -> Column:
    try:
        return await Column.objects.get(id=id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such column")


async def _get_task(id: int) -> Task:
    try:
        return await Task.objects.get(id=id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such task")


async def _get_project_group(id: int) -> ProjectGroup:
    try:
        return await ProjectGroup.objects.get(id=id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such project group")


async def _get_project_member(group_id: int, user_id: int) -> ProjectMember:
    try:
        return await ProjectMember.objects.get(group_id=group_id, user_id=user_id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such project member")


async def _next_position(model, filter_kwargs: dict) -> int:
    """Return the next available position for a child model query."""
    existing = await model.objects.filter(**filter_kwargs).all()
    if not existing:
        return 0
    return max((getattr(item, "position", 0) for item in existing), default=0) + 1


async def _validate_assignee(assignee_id: int | None) -> None:
    if assignee_id is None:
        return
    if User.dbtype() != "sql":
        raise HTTPException(
            status_code=400,
            detail="Task assignment is not supported with LDAP users",
        )
    try:
        await User.objects.get(id=assignee_id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such assignee")


async def _validate_parent(parent_id: int | None, task_id: int | None = None) -> None:
    if parent_id is None:
        return
    if task_id is not None and parent_id == task_id:
        raise HTTPException(status_code=400, detail="Task cannot be its own parent")
    try:
        await Task.objects.get(id=parent_id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such parent task")


async def _check_project_name_unique(name: str, exclude_id: int | None = None) -> None:
    existing = await Project.objects.filter(name=name).all()
    if any(item.id != exclude_id for item in existing):
        raise HTTPException(status_code=409, detail="Project name already exists")


async def _check_board_name_unique(
    project_id: int, name: str, exclude_id: int | None = None
) -> None:
    existing = await Board.objects.filter(project_id=project_id, name=name).all()
    if any(item.id != exclude_id for item in existing):
        raise HTTPException(
            status_code=409, detail="Board name already exists in this project"
        )


async def _check_column_name_unique(
    board_id: int, name: str, exclude_id: int | None = None
) -> None:
    existing = await Column.objects.filter(board_id=board_id, name=name).all()
    if any(item.id != exclude_id for item in existing):
        raise HTTPException(
            status_code=409, detail="Column name already exists in this board"
        )


async def _check_project_group_name_unique(
    project_id: int, name: str, exclude_id: int | None = None
) -> None:
    existing = await ProjectGroup.objects.filter(project_id=project_id, name=name).all()
    if any(item.id != exclude_id for item in existing):
        raise HTTPException(
            status_code=409, detail="Group name already exists in this project"
        )


async def _validate_project_group_member(group_id: int, user_id: int) -> None:
    try:
        await User.objects.get(id=user_id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such user")


async def _get_project_group_permissions(group_id: int) -> list[str]:
    permissions = await ProjectGroupPermission.objects.filter(group_id=group_id).all()
    return [p.permission for p in permissions]


async def _set_project_group_permissions(group_id: int, permissions: list[str]) -> None:
    existing = await ProjectGroupPermission.objects.filter(group_id=group_id).all()
    for perm in existing:
        await perm.delete()
    for permission in permissions:
        await ProjectGroupPermission.objects.create(
            group_id=group_id, permission=permission
        )


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@route("/projects", tags=tags)
class ProjectListAPI:
    @staticmethod
    @description("Get projects")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(project_perms),
    ) -> Page[ProjectResponse]:
        return await paginate(Project.objects, page, perpage)

    @staticmethod
    @description("Create project")
    async def post(
        data: ProjectCreate,
        user: User = Depends(project_perms),
    ) -> ProjectResponse:
        await _check_project_name_unique(data.name)
        now = datetime.utcnow()
        project = await Project.objects.create(
            name=data.name,
            description=data.description,
            created_by_id=getattr(user, "id", None),
            created_at=now,
            updated_at=now,
        )
        return ProjectResponse.model_validate(project)


@route("/projects/{id}", tags=tags)
class ProjectDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(project_perms)) -> ProjectResponse:
        project = await _get_project(id)
        return ProjectResponse.model_validate(project)

    @staticmethod
    async def patch(
        id: int,
        data: ProjectOptional,
        _: User = Depends(project_perms),
    ) -> ProjectResponse:
        project = await _get_project(id)
        if data.name:
            await _check_project_name_unique(data.name, exclude_id=id)
        await project.patch(data)
        return ProjectResponse.model_validate(project)

    @staticmethod
    async def delete(id: int, _: User = Depends(project_perms)) -> ProjectResponse:
        project = await _get_project(id)
        await project.delete()
        return ProjectResponse.model_validate(project)


# ---------------------------------------------------------------------------
# Boards
# ---------------------------------------------------------------------------


@route("/projects/{project_id}/boards", tags=tags)
class ProjectBoardListAPI:
    @staticmethod
    @description("Get project boards")
    async def get(
        project_id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(project_perms),
    ) -> Page[BoardResponse]:
        await _get_project(project_id)
        return await paginate(
            Board.objects.filter(project_id=project_id),
            page,
            perpage,
        )

    @staticmethod
    @description("Create board")
    async def post(
        project_id: int,
        data: BoardCreate,
        _: User = Depends(project_perms),
    ) -> BoardResponse:
        await _get_project(project_id)
        await _check_board_name_unique(project_id, data.name)
        now = datetime.utcnow()
        board = await Board.objects.create(
            project_id=project_id,
            name=data.name,
            description=data.description,
            created_at=now,
            updated_at=now,
        )
        return BoardResponse.model_validate(board)


@route("/boards/{id}", tags=tags)
class BoardDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(project_perms)) -> BoardResponse:
        board = await _get_board(id)
        return BoardResponse.model_validate(board)

    @staticmethod
    async def patch(
        id: int,
        data: BoardOptional,
        _: User = Depends(project_perms),
    ) -> BoardResponse:
        board = await _get_board(id)
        if data.name:
            await _check_board_name_unique(board.project_id, data.name, exclude_id=id)
        await board.patch(data)
        return BoardResponse.model_validate(board)

    @staticmethod
    async def delete(id: int, _: User = Depends(project_perms)) -> BoardResponse:
        board = await _get_board(id)
        await board.delete()
        return BoardResponse.model_validate(board)


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------


@route("/boards/{board_id}/columns", tags=tags)
class BoardColumnListAPI:
    @staticmethod
    @description("Get board columns")
    async def get(
        board_id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(project_perms),
    ) -> Page[ColumnResponse]:
        await _get_board(board_id)
        return await paginate(
            Column.objects.filter(board_id=board_id).order_by("position"),
            page,
            perpage,
        )

    @staticmethod
    @description("Create column")
    async def post(
        board_id: int,
        data: ColumnCreate,
        _: User = Depends(project_perms),
    ) -> ColumnResponse:
        await _get_board(board_id)
        await _check_column_name_unique(board_id, data.name)
        position = data.position
        if position is None:
            position = await _next_position(Column, {"board_id": board_id})
        now = datetime.utcnow()
        column = await Column.objects.create(
            board_id=board_id,
            name=data.name,
            position=position,
            created_at=now,
            updated_at=now,
        )
        return ColumnResponse.model_validate(column)


@route("/columns/{id}", tags=tags)
class ColumnDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(project_perms)) -> ColumnResponse:
        column = await _get_column(id)
        return ColumnResponse.model_validate(column)

    @staticmethod
    async def patch(
        id: int,
        data: ColumnOptional,
        _: User = Depends(project_perms),
    ) -> ColumnResponse:
        column = await _get_column(id)
        if data.name:
            await _check_column_name_unique(column.board_id, data.name, exclude_id=id)
        await column.patch(data)
        return ColumnResponse.model_validate(column)

    @staticmethod
    async def delete(id: int, _: User = Depends(project_perms)) -> ColumnResponse:
        column = await _get_column(id)
        await column.delete()
        return ColumnResponse.model_validate(column)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@route("/columns/{column_id}/tasks", tags=tags)
class ColumnTaskListAPI:
    @staticmethod
    @description("Get column tasks")
    async def get(
        column_id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(project_perms),
    ) -> Page[TaskResponse]:
        await _get_column(column_id)
        return await paginate(
            Task.objects.filter(column_id=column_id).order_by("position"),
            page,
            perpage,
        )

    @staticmethod
    @description("Create task")
    async def post(
        column_id: int,
        data: TaskCreate,
        _: User = Depends(project_perms),
    ) -> TaskResponse:
        await _get_column(column_id)
        await _validate_assignee(data.assignee_id)
        await _validate_parent(data.parent_id)
        position = data.position
        if position is None:
            position = await _next_position(Task, {"column_id": column_id})
        now = datetime.utcnow()
        task = await Task.objects.create(
            column_id=column_id,
            title=data.title,
            description=data.description,
            position=position,
            assignee_id=data.assignee_id,
            parent_id=data.parent_id,
            created_at=now,
            updated_at=now,
        )
        return TaskResponse.model_validate(task)


@route("/tasks/{id}", tags=tags)
class TaskDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(project_perms)) -> TaskDetailResponse:
        task = await _get_task(id)
        children = await Task.objects.filter(parent_id=id).order_by("position").all()
        parent = None
        if task.parent_id is not None:
            try:
                parent = await Task.objects.get(id=task.parent_id)
            except oxyde.NotFoundError:
                parent = None
        data = TaskResponse.model_validate(task).model_dump()
        data["children"] = [TaskResponse.model_validate(child) for child in children]
        data["parent"] = TaskResponse.model_validate(parent) if parent else None
        return TaskDetailResponse(**data)

    @staticmethod
    async def patch(
        id: int,
        data: TaskOptional,
        _: User = Depends(project_perms),
    ) -> TaskResponse:
        task = await _get_task(id)
        update = data.model_dump(exclude_none=True)

        if "column_id" in update:
            await _get_column(update["column_id"])
            task.column_id = update.pop("column_id")

        if "assignee_id" in update:
            await _validate_assignee(update["assignee_id"])
            task.assignee_id = update.pop("assignee_id")

        if "parent_id" in update:
            await _validate_parent(update["parent_id"], task_id=id)
            task.parent_id = update.pop("parent_id")

        for key, value in update.items():
            setattr(task, key, value)

        task.updated_at = datetime.utcnow()
        await task.save(
            update_fields=set(update.keys())
            | {"column_id", "assignee_id", "parent_id", "updated_at"}
        )
        return TaskResponse.model_validate(task)

    @staticmethod
    async def delete(id: int, _: User = Depends(project_perms)) -> TaskResponse:
        task = await _get_task(id)
        await task.delete()
        return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------------
# Project Groups
# ---------------------------------------------------------------------------


@route("/projects/{project_id}/groups", tags=tags)
class ProjectGroupListAPI:
    @staticmethod
    @description("Get project groups")
    async def get(
        project_id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(project_perms),
    ) -> Page[ProjectGroupResponse]:
        await _get_project(project_id)
        result = await paginate(
            ProjectGroup.objects.filter(project_id=project_id),
            page,
            perpage,
        )
        for item in result.data:
            object.__setattr__(
                item, "permissions", await _get_project_group_permissions(item.id)
            )
        return result

    @staticmethod
    @description("Create project group")
    async def post(
        project_id: int,
        data: ProjectGroupCreate,
        _: User = Depends(project_perms),
    ) -> ProjectGroupResponse:
        await _get_project(project_id)
        await _check_project_group_name_unique(project_id, data.name)
        now = datetime.utcnow()
        group = await ProjectGroup.objects.create(
            project_id=project_id,
            name=data.name,
            description=data.description,
            created_at=now,
            updated_at=now,
        )
        await _set_project_group_permissions(group.id, data.permissions)
        object.__setattr__(
            group, "permissions", await _get_project_group_permissions(group.id)
        )
        return ProjectGroupResponse.model_validate(group)


@route("/project-groups/{id}", tags=tags)
class ProjectGroupDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(project_perms)) -> ProjectGroupResponse:
        group = await _get_project_group(id)
        object.__setattr__(
            group, "permissions", await _get_project_group_permissions(id)
        )
        return ProjectGroupResponse.model_validate(group)

    @staticmethod
    async def patch(
        id: int,
        data: ProjectGroupOptional,
        _: User = Depends(project_perms),
    ) -> ProjectGroupResponse:
        group = await _get_project_group(id)
        if data.name:
            await _check_project_group_name_unique(
                group.project_id, data.name, exclude_id=id
            )
        update = data.model_dump(exclude_none=True)
        if "permissions" in update:
            await _set_project_group_permissions(id, update.pop("permissions"))
        if update:
            await group.patch(ProjectGroupOptional(**update))
        object.__setattr__(
            group, "permissions", await _get_project_group_permissions(id)
        )
        return ProjectGroupResponse.model_validate(group)

    @staticmethod
    async def delete(id: int, _: User = Depends(project_perms)) -> ProjectGroupResponse:
        group = await _get_project_group(id)
        await group.delete()
        return ProjectGroupResponse.model_validate(group)


# ---------------------------------------------------------------------------
# Project Group Members
# ---------------------------------------------------------------------------


@route("/project-groups/{group_id}/members", tags=tags)
class ProjectGroupMemberListAPI:
    @staticmethod
    @description("Get project group members")
    async def get(
        group_id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(project_perms),
    ) -> Page[ProjectGroupMemberResponse]:
        await _get_project_group(group_id)
        return await paginate(
            ProjectMember.objects.filter(group_id=group_id),
            page,
            perpage,
        )

    @staticmethod
    @description("Add member to project group")
    async def post(
        group_id: int,
        data: ProjectGroupMemberCreate,
        _: User = Depends(project_perms),
    ) -> ProjectGroupMemberResponse:
        await _get_project_group(group_id)
        await _validate_project_group_member(group_id, data.user_id)
        now = datetime.utcnow()
        try:
            member = await ProjectMember.objects.create(
                group_id=group_id,
                user_id=data.user_id,
                created_at=now,
            )
        except oxyde.IntegrityError:
            raise HTTPException(status_code=409, detail="User already in group")
        return ProjectGroupMemberResponse.model_validate(member)


@route("/project-groups/{group_id}/members/{user_id}", tags=tags)
class ProjectGroupMemberDetailAPI:
    @staticmethod
    async def delete(
        group_id: int,
        user_id: int,
        _: User = Depends(project_perms),
    ) -> ProjectGroupMemberResponse:
        member = await _get_project_member(group_id, user_id)
        await member.delete()
        return ProjectGroupMemberResponse.model_validate(member)
