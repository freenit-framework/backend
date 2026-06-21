import pytest

from . import factories


@pytest.mark.asyncio
class TestProject:
    async def test_create_project(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        data = {"name": "Test Project", "description": "A test project"}
        response = client.post("/projects", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == data["name"]
        assert result["description"] == data["description"]
        assert result["created_by_id"] == user.id

    async def test_get_projects(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        response = client.get("/projects")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_get_project(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        response = client.get(f"/projects/{project.id}")
        assert response.status_code == 200
        assert response.json()["id"] == project.id

    async def test_update_project(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        data = {"name": "Updated Project"}
        response = client.patch(f"/projects/{project.id}", data=data)
        assert response.status_code == 200
        assert response.json()["name"] == data["name"]

    async def test_delete_project(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        response = client.delete(f"/projects/{project.id}")
        assert response.status_code == 200
        response = client.get(f"/projects/{project.id}")
        assert response.status_code == 404

    async def test_create_project_duplicate_name(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(name="Unique Project", created_by_id=user.id)
        await project.save()
        response = client.post("/projects", data={"name": "Unique Project"})
        assert response.status_code == 409

    async def test_update_project_duplicate_name(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project1 = factories.ProjectFactory(name="Project One", created_by_id=user.id)
        await project1.save()
        project2 = factories.ProjectFactory(name="Project Two", created_by_id=user.id)
        await project2.save()
        response = client.patch(
            f"/projects/{project2.id}", data={"name": "Project One"}
        )
        assert response.status_code == 409


@pytest.mark.asyncio
class TestBoard:
    async def test_create_board(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        data = {"name": "Test Board", "description": "A test board"}
        response = client.post(f"/projects/{project.id}/boards", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == data["name"]
        assert result["project_id"] == project.id

    async def test_get_boards(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        response = client.get(f"/projects/{project.id}/boards")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_get_board(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        response = client.get(f"/boards/{board.id}")
        assert response.status_code == 200
        assert response.json()["id"] == board.id

    async def test_update_board(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        data = {"name": "Updated Board"}
        response = client.patch(f"/boards/{board.id}", data=data)
        assert response.status_code == 200
        assert response.json()["name"] == data["name"]

    async def test_delete_board(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        response = client.delete(f"/boards/{board.id}")
        assert response.status_code == 200
        response = client.get(f"/boards/{board.id}")
        assert response.status_code == 404

    async def test_create_board_duplicate_name(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id, name="Board X")
        await board.save()
        response = client.post(
            f"/projects/{project.id}/boards", data={"name": "Board X"}
        )
        assert response.status_code == 409

    async def test_update_board_duplicate_name(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board1 = factories.BoardFactory(project_id=project.id, name="Board One")
        await board1.save()
        board2 = factories.BoardFactory(project_id=project.id, name="Board Two")
        await board2.save()
        response = client.patch(f"/boards/{board2.id}", data={"name": "Board One"})
        assert response.status_code == 409


@pytest.mark.asyncio
class TestColumn:
    async def test_create_column(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        data = {"name": "To Do"}
        response = client.post(f"/boards/{board.id}/columns", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == data["name"]
        assert result["board_id"] == board.id

    async def test_get_columns(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        response = client.get(f"/boards/{board.id}/columns")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_update_column(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        data = {"name": "In Progress", "position": 5}
        response = client.patch(f"/columns/{column.id}", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == data["name"]
        assert result["position"] == data["position"]

    async def test_delete_column(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        response = client.delete(f"/columns/{column.id}")
        assert response.status_code == 200
        response = client.get(f"/columns/{column.id}")
        assert response.status_code == 404

    async def test_create_column_duplicate_name(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id, name="Column X")
        await column.save()
        response = client.post(f"/boards/{board.id}/columns", data={"name": "Column X"})
        assert response.status_code == 409

    async def test_update_column_duplicate_name(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column1 = factories.ColumnFactory(board_id=board.id, name="Column One")
        await column1.save()
        column2 = factories.ColumnFactory(board_id=board.id, name="Column Two")
        await column2.save()
        response = client.patch(f"/columns/{column2.id}", data={"name": "Column One"})
        assert response.status_code == 409


@pytest.mark.asyncio
class TestTask:
    async def test_create_task(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        data = {"title": "Test Task", "description": "A test task"}
        response = client.post(f"/columns/{column.id}/tasks", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == data["title"]
        assert result["column_id"] == column.id

    async def test_get_tasks(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        task = factories.TaskFactory(column_id=column.id)
        await task.save()
        response = client.get(f"/columns/{column.id}/tasks")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_get_task(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        task = factories.TaskFactory(column_id=column.id)
        await task.save()
        response = client.get(f"/tasks/{task.id}")
        assert response.status_code == 200
        assert response.json()["id"] == task.id
        assert response.json()["children"] == []
        assert response.json()["parent"] is None

    async def test_get_task_includes_children(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        parent = factories.TaskFactory(column_id=column.id)
        await parent.save()
        child = factories.TaskFactory(column_id=column.id, parent_id=parent.id)
        await child.save()
        response = client.get(f"/tasks/{parent.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == parent.id
        assert len(data["children"]) == 1
        assert data["children"][0]["id"] == child.id

    async def test_get_task_includes_parent(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        parent = factories.TaskFactory(column_id=column.id)
        await parent.save()
        child = factories.TaskFactory(column_id=column.id, parent_id=parent.id)
        await child.save()
        response = client.get(f"/tasks/{child.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == child.id
        assert data["parent"]["id"] == parent.id

    async def test_update_task(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        task = factories.TaskFactory(column_id=column.id)
        await task.save()
        data = {"title": "Updated Task"}
        response = client.patch(f"/tasks/{task.id}", data=data)
        assert response.status_code == 200
        assert response.json()["title"] == data["title"]

    async def test_move_task_between_columns(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column1 = factories.ColumnFactory(board_id=board.id)
        await column1.save()
        column2 = factories.ColumnFactory(board_id=board.id)
        await column2.save()
        task = factories.TaskFactory(column=column1)
        await task.save()
        data = {"column_id": column2.id}
        response = client.patch(f"/tasks/{task.id}", data=data)
        assert response.status_code == 200
        assert response.json()["column_id"] == column2.id

    async def test_delete_task(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        task = factories.TaskFactory(column_id=column.id)
        await task.save()
        response = client.delete(f"/tasks/{task.id}")
        assert response.status_code == 200
        response = client.get(f"/tasks/{task.id}")
        assert response.status_code == 404

    async def test_create_task_with_parent(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        parent = factories.TaskFactory(column_id=column.id)
        await parent.save()
        response = client.post(
            f"/columns/{column.id}/tasks",
            data={"title": "Child Task", "parent_id": parent.id},
        )
        assert response.status_code == 200
        assert response.json()["parent_id"] == parent.id

    async def test_task_self_parent_rejected(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        board = factories.BoardFactory(project_id=project.id)
        await board.save()
        column = factories.ColumnFactory(board_id=board.id)
        await column.save()
        task = factories.TaskFactory(column_id=column.id)
        await task.save()
        response = client.patch(f"/tasks/{task.id}", data={"parent_id": task.id})
        assert response.status_code == 400


@pytest.mark.asyncio
class TestProjectGroup:
    async def test_create_project_group(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        data = {"name": "Test Group", "description": "A test group"}
        response = client.post(f"/projects/{project.id}/groups", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == data["name"]
        assert result["description"] == data["description"]
        assert result["project_id"] == project.id

    async def test_get_project_groups(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        response = client.get(f"/projects/{project.id}/groups")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_get_project_group(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        response = client.get(f"/project-groups/{group.id}")
        assert response.status_code == 200
        assert response.json()["id"] == group.id

    async def test_update_project_group(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        data = {"name": "Updated Group"}
        response = client.patch(f"/project-groups/{group.id}", data=data)
        assert response.status_code == 200
        assert response.json()["name"] == data["name"]

    async def test_delete_project_group(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        response = client.delete(f"/project-groups/{group.id}")
        assert response.status_code == 200
        response = client.get(f"/project-groups/{group.id}")
        assert response.status_code == 404

    async def test_create_project_group_duplicate_name(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id, name="Group X")
        await group.save()
        response = client.post(
            f"/projects/{project.id}/groups", data={"name": "Group X"}
        )
        assert response.status_code == 409

    async def test_update_project_group_duplicate_name(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group1 = factories.ProjectGroupFactory(project_id=project.id, name="Group One")
        await group1.save()
        group2 = factories.ProjectGroupFactory(project_id=project.id, name="Group Two")
        await group2.save()
        response = client.patch(
            f"/project-groups/{group2.id}", data={"name": "Group One"}
        )
        assert response.status_code == 409


@pytest.mark.asyncio
class TestProjectGroupMember:
    async def test_add_project_group_member(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        response = client.post(
            f"/project-groups/{group.id}/members", data={"user_id": user.id}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["group_id"] == group.id
        assert result["user_id"] == user.id

    async def test_get_project_group_members(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        member = factories.ProjectMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.get(f"/project-groups/{group.id}/members")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_remove_project_group_member(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        member = factories.ProjectMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.delete(f"/project-groups/{group.id}/members/{user.id}")
        assert response.status_code == 200
        response = client.get(f"/project-groups/{group.id}/members")
        assert response.json()["total"] == 0

    async def test_add_duplicate_project_group_member(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        member = factories.ProjectMemberFactory(group_id=group.id, user_id=user.id)
        await member.save()
        response = client.post(
            f"/project-groups/{group.id}/members", data={"user_id": user.id}
        )
        assert response.status_code == 409


@pytest.mark.asyncio
class TestProjectGroupPermissions:
    async def test_create_project_group_with_permissions(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        data = {
            "name": "Test Group",
            "description": "A test group",
            "permissions": ["create_board", "delete_board"],
        }
        response = client.post(f"/projects/{project.id}/groups", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["permissions"] == data["permissions"]

    async def test_get_project_group_with_permissions(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        perm = factories.ProjectGroupPermissionFactory(
            group_id=group.id, permission="create_column"
        )
        await perm.save()
        response = client.get(f"/project-groups/{group.id}")
        assert response.status_code == 200
        assert "create_column" in response.json()["permissions"]

    async def test_update_project_group_permissions(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        project = factories.ProjectFactory(created_by_id=user.id)
        await project.save()
        group = factories.ProjectGroupFactory(project_id=project.id)
        await group.save()
        perm = factories.ProjectGroupPermissionFactory(
            group_id=group.id, permission="create_column"
        )
        await perm.save()
        data = {"permissions": ["create_project", "delete_project"]}
        response = client.patch(f"/project-groups/{group.id}", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["permissions"] == data["permissions"]
