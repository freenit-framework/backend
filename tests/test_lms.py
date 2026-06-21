import pytest

from . import factories


@pytest.mark.asyncio
class TestCourse:
    async def test_create_course(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        data = {"name": "Test Course", "description": "A test course"}
        response = client.post("/courses", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == data["name"]
        assert result["description"] == data["description"]
        assert result["created_by_id"] == user.id

    async def test_get_courses(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory(created_by_id=user.id)
        await course.save()
        response = client.get("/courses")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_get_course(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory(created_by_id=user.id)
        await course.save()
        response = client.get(f"/courses/{course.id}")
        assert response.status_code == 200
        assert response.json()["id"] == course.id

    async def test_update_course(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        data = {"name": "Updated Course"}
        response = client.patch(f"/courses/{course.id}", data=data)
        assert response.status_code == 200
        assert response.json()["name"] == data["name"]

    async def test_delete_course(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.delete(f"/courses/{course.id}")
        assert response.status_code == 200
        response = client.get(f"/courses/{course.id}")
        assert response.status_code == 404

    async def test_create_course_duplicate_name(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory(name="Unique Course")
        await course.save()
        response = client.post("/courses", data={"name": "Unique Course"})
        assert response.status_code == 409

    async def test_update_course_duplicate_name(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course1 = factories.CourseFactory(name="Course One")
        await course1.save()
        course2 = factories.CourseFactory(name="Course Two")
        await course2.save()
        group = factories.CourseGroupFactory(course_id=course2.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.patch(f"/courses/{course2.id}", data={"name": "Course One"})
        assert response.status_code == 409


@pytest.mark.asyncio
class TestLecture:
    async def test_create_lecture(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        data = {"title": "Test Lecture", "content": "A test lecture"}
        response = client.post(f"/courses/{course.id}/lectures", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == data["title"]
        assert result["course_id"] == course.id
        assert result["state"] == "draft"

    async def test_create_lecture_with_state(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        data = {"title": "Public Lecture", "state": "published_public"}
        response = client.post(f"/courses/{course.id}/lectures", data=data)
        assert response.status_code == 200
        assert response.json()["state"] == "published_public"

    async def test_get_lectures(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        lecture = factories.LectureFactory(
            course_id=course.id, state="published_public"
        )
        await lecture.save()
        response = client.get(f"/courses/{course.id}/lectures")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_get_lecture(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        lecture = factories.LectureFactory(
            course_id=course.id, state="published_public"
        )
        await lecture.save()
        response = client.get(f"/lectures/{lecture.id}")
        assert response.status_code == 200
        assert response.json()["id"] == lecture.id

    async def test_draft_lecture_hidden_from_non_editor(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        lecture = factories.LectureFactory(course_id=course.id, state="draft")
        await lecture.save()
        response = client.get(f"/lectures/{lecture.id}")
        assert response.status_code == 403
        response = client.get(f"/courses/{course.id}/lectures")
        assert response.json()["total"] == 0

    async def test_published_private_lecture_requires_view_permission(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        lecture = factories.LectureFactory(
            course_id=course.id, state="published_private"
        )
        await lecture.save()
        response = client.get(f"/lectures/{lecture.id}")
        assert response.status_code == 403

    async def test_published_private_lecture_visible_with_view_permission(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        lecture = factories.LectureFactory(
            course_id=course.id, state="published_private"
        )
        await lecture.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="view"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.get(f"/lectures/{lecture.id}")
        assert response.status_code == 200
        assert response.json()["id"] == lecture.id

    async def test_update_lecture(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        lecture = factories.LectureFactory(course_id=course.id)
        await lecture.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        data = {"title": "Updated Lecture", "state": "published_public"}
        response = client.patch(f"/lectures/{lecture.id}", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == data["title"]
        assert result["state"] == "published_public"

    async def test_delete_lecture(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        lecture = factories.LectureFactory(course_id=course.id)
        await lecture.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.delete(f"/lectures/{lecture.id}")
        assert response.status_code == 200
        response = client.get(f"/lectures/{lecture.id}")
        assert response.status_code == 404

    async def test_create_lecture_duplicate_title(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        lecture = factories.LectureFactory(course_id=course.id, title="Lecture X")
        await lecture.save()
        response = client.post(
            f"/courses/{course.id}/lectures", data={"title": "Lecture X"}
        )
        assert response.status_code == 409


@pytest.mark.asyncio
class TestCourseGroup:
    async def test_create_course_group(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        data = {"name": "Test Group", "description": "A test group"}
        response = client.post(f"/courses/{course.id}/groups", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == data["name"]
        assert result["course_id"] == course.id

    async def test_get_course_groups(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        response = client.get(f"/courses/{course.id}/groups")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_get_course_group(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        response = client.get(f"/course-groups/{group.id}")
        assert response.status_code == 200
        assert response.json()["id"] == group.id
        assert "edit" in response.json()["permissions"]

    async def test_update_course_group(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        data = {"name": "Updated Group"}
        response = client.patch(f"/course-groups/{group.id}", data=data)
        assert response.status_code == 200
        assert response.json()["name"] == data["name"]

    async def test_delete_course_group(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.delete(f"/course-groups/{group.id}")
        assert response.status_code == 200
        response = client.get(f"/course-groups/{group.id}")
        assert response.status_code == 404

    async def test_create_course_group_duplicate_name(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id, name="Group X")
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.post(f"/courses/{course.id}/groups", data={"name": "Group X"})
        assert response.status_code == 409


@pytest.mark.asyncio
class TestCourseGroupMember:
    async def test_add_course_group_member(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        target = factories.User()
        await target.save()
        response = client.post(
            f"/course-groups/{group.id}/members", data={"user_id": target.id}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["group_id"] == group.id
        assert result["user_id"] == target.id

    async def test_get_course_group_members(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.get(f"/course-groups/{group.id}/members")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_remove_course_group_member(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.delete(f"/course-groups/{group.id}/members/{user.id}")
        assert response.status_code == 200
        response = client.get(f"/course-groups/{group.id}/members")
        assert response.json()["total"] == 0

    async def test_add_duplicate_course_group_member(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.post(
            f"/course-groups/{group.id}/members", data={"user_id": user.id}
        )
        assert response.status_code == 409


@pytest.mark.asyncio
class TestCourseGroupPermissions:
    async def test_create_course_group_with_permissions(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        data = {
            "name": "Test Group",
            "description": "A test group",
            "permissions": ["edit"],
        }
        response = client.post(f"/courses/{course.id}/groups", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["permissions"] == data["permissions"]

    async def test_update_course_group_permissions(self, client):
        user = factories.User(admin=True)
        await user.save()
        client.login(user=user)
        course = factories.CourseFactory()
        await course.save()
        group = factories.CourseGroupFactory(course_id=course.id)
        await group.save()
        perm = factories.CourseGroupPermissionFactory(
            group_id=group.id, permission="edit"
        )
        await perm.save()
        member = factories.CourseMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        data = {"permissions": []}
        response = client.patch(f"/course-groups/{group.id}", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["permissions"] == data["permissions"]
