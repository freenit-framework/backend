from datetime import datetime

import oxyde
import pydantic
from fastapi import Depends, Header, HTTPException

from freenit.api.router import route
from freenit.decorators import description
from freenit.models.lms import (
    Course,
    CourseGroup,
    CourseGroupOptional,
    CourseGroupPermission,
    CourseMember,
    CourseOptional,
    Lecture,
    LectureOptional,
    LectureState,
)
from freenit.models.pagination import Page, paginate
from freenit.models.user import User
from freenit.permissions import lms_perms

tags = ["lms"]


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class CourseCreate(pydantic.BaseModel):
    name: str
    description: str | None = None


class CourseResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    created_by_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LectureCreate(pydantic.BaseModel):
    title: str
    content: str | None = None
    position: int | None = None
    state: LectureState | None = None


class LectureResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    content: str | None = None
    position: int
    state: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CourseGroupCreate(pydantic.BaseModel):
    name: str
    description: str | None = None
    permissions: list[str] = []


class CourseGroupResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    course_id: int
    name: str
    description: str | None = None
    permissions: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CourseMemberCreate(pydantic.BaseModel):
    user_id: int


class CourseMemberResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    group_id: int
    user_id: int
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_course(id: int) -> Course:
    try:
        return await Course.objects.get(id=id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such course")


async def _get_lecture(id: int) -> Lecture:
    try:
        return await Lecture.objects.get(id=id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such lecture")


async def _get_group(id: int) -> CourseGroup:
    try:
        return await CourseGroup.objects.get(id=id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such course group")


async def _get_member(group_id: int, user_id: int) -> CourseMember:
    try:
        return await CourseMember.objects.get(group_id=group_id, user_id=user_id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such course member")


async def _next_position(model, filter_kwargs: dict) -> int:
    existing = await model.objects.filter(**filter_kwargs).all()
    if not existing:
        return 0
    return max((getattr(item, "position", 0) for item in existing), default=0) + 1


async def _check_course_name_unique(name: str, exclude_id: int | None = None) -> None:
    existing = await Course.objects.filter(name=name).all()
    if any(item.id != exclude_id for item in existing):
        raise HTTPException(status_code=409, detail="Course name already exists")


async def _check_group_name_unique(
    course_id: int, name: str, exclude_id: int | None = None
) -> None:
    existing = await CourseGroup.objects.filter(course_id=course_id, name=name).all()
    if any(item.id != exclude_id for item in existing):
        raise HTTPException(
            status_code=409, detail="Group name already exists in this course"
        )


async def _check_lecture_title_unique(
    course_id: int, title: str, exclude_id: int | None = None
) -> None:
    existing = await Lecture.objects.filter(course_id=course_id, title=title).all()
    if any(item.id != exclude_id for item in existing):
        raise HTTPException(
            status_code=409, detail="Lecture title already exists in this course"
        )


async def _validate_member(group_id: int, user_id: int) -> None:
    try:
        await User.objects.get(id=user_id)
    except oxyde.NotFoundError:
        raise HTTPException(status_code=404, detail="No such user")


async def _get_group_permissions(group_id: int) -> list[str]:
    permissions = await CourseGroupPermission.objects.filter(group_id=group_id).all()
    return [p.permission for p in permissions]


async def _set_group_permissions(group_id: int, permissions: list[str]) -> None:
    existing = await CourseGroupPermission.objects.filter(group_id=group_id).all()
    for perm in existing:
        await perm.delete()
    for permission in permissions:
        await CourseGroupPermission.objects.create(
            group_id=group_id, permission=permission
        )


async def _user_has_course_permission(
    user: User, course_id: int, permission: str
) -> bool:
    if user.admin:
        return True
    groups = await CourseGroup.objects.filter(course_id=course_id).all()
    group_ids = [g.id for g in groups]
    if not group_ids:
        return False
    members = await CourseMember.objects.filter(
        group_id__in=group_ids, user_id=user.id
    ).all()
    if not members:
        return False
    member_group_ids = [m.group_id for m in members]
    perms = await CourseGroupPermission.objects.filter(
        group_id__in=member_group_ids, permission=permission
    ).all()
    return len(perms) > 0


async def _require_course_permission(
    user: User, course_id: int, permission: str
) -> None:
    if not await _user_has_course_permission(user, course_id, permission):
        raise HTTPException(status_code=403, detail="Forbidden")


async def _visible_lecture_states(user: User, course_id: int) -> list[str]:
    states = [LectureState.PUBLISHED_PUBLIC]
    if await _user_has_course_permission(user, course_id, "view"):
        states.append(LectureState.PUBLISHED_PRIVATE)
    if await _user_has_course_permission(user, course_id, "edit"):
        states.append(LectureState.DRAFT)
    return states


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------


@route("/courses", tags=tags)
class CourseListAPI:
    @staticmethod
    @description("Get courses")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(lms_perms),
    ) -> Page[CourseResponse]:
        return await paginate(Course.objects, page, perpage)

    @staticmethod
    @description("Create course")
    async def post(
        data: CourseCreate,
        user: User = Depends(lms_perms),
    ) -> CourseResponse:
        await _check_course_name_unique(data.name)
        now = datetime.utcnow()
        course = await Course.objects.create(
            name=data.name,
            description=data.description,
            created_by_id=getattr(user, "id", None),
            created_at=now,
            updated_at=now,
        )
        return CourseResponse.model_validate(course)


@route("/courses/{id}", tags=tags)
class CourseDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(lms_perms)) -> CourseResponse:
        course = await _get_course(id)
        return CourseResponse.model_validate(course)

    @staticmethod
    async def patch(
        id: int,
        data: CourseOptional,
        user: User = Depends(lms_perms),
    ) -> CourseResponse:
        course = await _get_course(id)
        await _require_course_permission(user, id, "edit")
        if data.name:
            await _check_course_name_unique(data.name, exclude_id=id)
        await course.patch(data)
        return CourseResponse.model_validate(course)

    @staticmethod
    async def delete(id: int, user: User = Depends(lms_perms)) -> CourseResponse:
        course = await _get_course(id)
        await _require_course_permission(user, id, "edit")
        await course.delete()
        return CourseResponse.model_validate(course)


# ---------------------------------------------------------------------------
# Lectures
# ---------------------------------------------------------------------------


@route("/courses/{course_id}/lectures", tags=tags)
class CourseLectureListAPI:
    @staticmethod
    @description("Get course lectures")
    async def get(
        course_id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        user: User = Depends(lms_perms),
    ) -> Page[LectureResponse]:
        await _get_course(course_id)
        states = await _visible_lecture_states(user, course_id)
        return await paginate(
            Lecture.objects.filter(course_id=course_id, state__in=states).order_by(
                "position"
            ),
            page,
            perpage,
        )

    @staticmethod
    @description("Create lecture")
    async def post(
        course_id: int,
        data: LectureCreate,
        user: User = Depends(lms_perms),
    ) -> LectureResponse:
        await _get_course(course_id)
        await _require_course_permission(user, course_id, "edit")
        await _check_lecture_title_unique(course_id, data.title)
        position = data.position
        if position is None:
            position = await _next_position(Lecture, {"course_id": course_id})
        now = datetime.utcnow()
        lecture = await Lecture.objects.create(
            course_id=course_id,
            title=data.title,
            content=data.content,
            position=position,
            state=data.state or LectureState.DRAFT,
            created_at=now,
            updated_at=now,
        )
        return LectureResponse.model_validate(lecture)


@route("/lectures/{id}", tags=tags)
class LectureDetailAPI:
    @staticmethod
    async def get(id: int, user: User = Depends(lms_perms)) -> LectureResponse:
        lecture = await _get_lecture(id)
        if lecture.state == LectureState.DRAFT:
            await _require_course_permission(user, lecture.course_id, "edit")
        elif lecture.state == LectureState.PUBLISHED_PRIVATE:
            await _require_course_permission(user, lecture.course_id, "view")
        return LectureResponse.model_validate(lecture)

    @staticmethod
    async def patch(
        id: int,
        data: LectureOptional,
        user: User = Depends(lms_perms),
    ) -> LectureResponse:
        lecture = await _get_lecture(id)
        await _require_course_permission(user, lecture.course_id, "edit")
        if data.title:
            await _check_lecture_title_unique(
                lecture.course_id, data.title, exclude_id=id
            )
        await lecture.patch(data)
        return LectureResponse.model_validate(lecture)

    @staticmethod
    async def delete(id: int, user: User = Depends(lms_perms)) -> LectureResponse:
        lecture = await _get_lecture(id)
        await _require_course_permission(user, lecture.course_id, "edit")
        await lecture.delete()
        return LectureResponse.model_validate(lecture)


# ---------------------------------------------------------------------------
# Course Groups
# ---------------------------------------------------------------------------


@route("/courses/{course_id}/groups", tags=tags)
class CourseGroupListAPI:
    @staticmethod
    @description("Get course groups")
    async def get(
        course_id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(lms_perms),
    ) -> Page[CourseGroupResponse]:
        await _get_course(course_id)
        result = await paginate(
            CourseGroup.objects.filter(course_id=course_id),
            page,
            perpage,
        )
        for item in result.data:
            object.__setattr__(
                item, "permissions", await _get_group_permissions(item.id)
            )
        return result

    @staticmethod
    @description("Create course group")
    async def post(
        course_id: int,
        data: CourseGroupCreate,
        user: User = Depends(lms_perms),
    ) -> CourseGroupResponse:
        await _get_course(course_id)
        await _require_course_permission(user, course_id, "edit")
        await _check_group_name_unique(course_id, data.name)
        now = datetime.utcnow()
        group = await CourseGroup.objects.create(
            course_id=course_id,
            name=data.name,
            description=data.description,
            created_at=now,
            updated_at=now,
        )
        await _set_group_permissions(group.id, data.permissions)
        object.__setattr__(group, "permissions", await _get_group_permissions(group.id))
        return CourseGroupResponse.model_validate(group)


@route("/course-groups/{id}", tags=tags)
class CourseGroupDetailAPI:
    @staticmethod
    async def get(id: int, _: User = Depends(lms_perms)) -> CourseGroupResponse:
        group = await _get_group(id)
        object.__setattr__(group, "permissions", await _get_group_permissions(id))
        return CourseGroupResponse.model_validate(group)

    @staticmethod
    async def patch(
        id: int,
        data: CourseGroupOptional,
        user: User = Depends(lms_perms),
    ) -> CourseGroupResponse:
        group = await _get_group(id)
        await _require_course_permission(user, group.course_id, "edit")
        if data.name:
            await _check_group_name_unique(group.course_id, data.name, exclude_id=id)
        update = data.model_dump(exclude_none=True)
        if "permissions" in update:
            await _set_group_permissions(id, update.pop("permissions"))
        if update:
            await group.patch(CourseGroupOptional(**update))
        object.__setattr__(group, "permissions", await _get_group_permissions(id))
        return CourseGroupResponse.model_validate(group)

    @staticmethod
    async def delete(id: int, user: User = Depends(lms_perms)) -> CourseGroupResponse:
        group = await _get_group(id)
        await _require_course_permission(user, group.course_id, "edit")
        await group.delete()
        return CourseGroupResponse.model_validate(group)


# ---------------------------------------------------------------------------
# Course Group Members
# ---------------------------------------------------------------------------


@route("/course-groups/{group_id}/members", tags=tags)
class CourseGroupMemberListAPI:
    @staticmethod
    @description("Get course group members")
    async def get(
        group_id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        _: User = Depends(lms_perms),
    ) -> Page[CourseMemberResponse]:
        await _get_group(group_id)
        return await paginate(
            CourseMember.objects.filter(group_id=group_id),
            page,
            perpage,
        )

    @staticmethod
    @description("Add member to course group")
    async def post(
        group_id: int,
        data: CourseMemberCreate,
        user: User = Depends(lms_perms),
    ) -> CourseMemberResponse:
        group = await _get_group(group_id)
        await _require_course_permission(user, group.course_id, "edit")
        await _validate_member(group_id, data.user_id)
        now = datetime.utcnow()
        try:
            member = await CourseMember.objects.create(
                group_id=group_id,
                user_id=data.user_id,
                created_at=now,
            )
        except oxyde.IntegrityError:
            raise HTTPException(status_code=409, detail="User already in group")
        return CourseMemberResponse.model_validate(member)


@route("/course-groups/{group_id}/members/{user_id}", tags=tags)
class CourseGroupMemberDetailAPI:
    @staticmethod
    async def delete(
        group_id: int,
        user_id: int,
        user: User = Depends(lms_perms),
    ) -> CourseMemberResponse:
        group = await _get_group(group_id)
        await _require_course_permission(user, group.course_id, "edit")
        member = await _get_member(group_id, user_id)
        await member.delete()
        return CourseMemberResponse.model_validate(member)
