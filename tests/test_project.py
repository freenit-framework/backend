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
        response = client.patch(f"/projects/{project2.id}", data={"name": "Project One"})
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
        response = client.post(
            f"/boards/{board.id}/columns", data={"name": "Column X"}
        )
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
        response = client.patch(
            f"/tasks/{task.id}", data={"parent_id": task.id}
        )
        assert response.status_code == 400
