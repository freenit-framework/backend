import subprocess  # nosec: B404
import tempfile
from pathlib import Path

import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from freenit.git import repo as git_repo
from freenit.git import store
from freenit.git.hooks import post_receive
from freenit.models.git import GitRepo
from freenit.models.user import User

from . import factories


def _init_temp_repo(message: str = "init"):
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name)
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True)  # nosec
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
    )  # nosec
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=path,
        check=True,
    )  # nosec
    (path / "README.md").write_text("# Hello\n")
    (path / "src" / "main.py").parent.mkdir(parents=True, exist_ok=True)
    (path / "src" / "main.py").write_text("print('hello')\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)  # nosec
    subprocess.run(["git", "commit", "-m", message], cwd=path, check=True)  # nosec
    return tmp


def _create_project(client, name: str | None = None):
    if name is None:
        name = f"git-project-{tempfile.mkdtemp(prefix='').split('/')[-1]}"
    response = client.post("/projects", {"name": name})
    assert response.status_code == 200  # nosec
    return response.json()["id"]


def _tmp_dir() -> str:
    return tempfile.mkdtemp(prefix="freenit-git-")


class TestGit:
    @pytest.mark.asyncio
    async def test_create_and_list_repos(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        response = client.post(
            "/git/repos",
            {
                "name": "test-repo",
                "path": _tmp_dir(),
                "project_id": project_id,
                "description": "A test repo",
                "public": True,
            },
        )
        assert response.status_code == 200  # nosec
        data = response.json()
        assert data["name"] == "test-repo"  # nosec
        assert data["public"] is True  # nosec

        response = client.get("/git/repos")
        assert response.status_code == 200  # nosec
        data = response.json()
        assert data["total"] == 1  # nosec
        assert data["data"][0]["name"] == "test-repo"  # nosec

    @pytest.mark.asyncio
    async def test_public_repos(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        client.post(
            "/git/repos",
            {
                "name": "public-repo",
                "path": _tmp_dir(),
                "project_id": project_id,
                "public": True,
            },
        )
        client.post(
            "/git/repos",
            {
                "name": "private-repo",
                "path": _tmp_dir(),
                "project_id": project_id,
                "public": False,
            },
        )

        # No authentication required for public list.
        client.cookies = {}
        response = client.get("/git/repos/public")
        assert response.status_code == 200  # nosec
        data = response.json()
        assert data["total"] == 1  # nosec
        assert data["data"][0]["name"] == "public-repo"  # nosec

    @pytest.mark.asyncio
    async def test_update_and_delete_repo(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        response = client.post(
            "/git/repos",
            {"name": "mutable-repo", "path": _tmp_dir(), "project_id": project_id},
        )
        repo_id = response.json()["id"]

        response = client.patch(
            f"/git/repos/{repo_id}",
            {"description": "Updated description"},
        )
        assert response.status_code == 200  # nosec
        assert response.json()["description"] == "Updated description"  # nosec

        response = client.delete(f"/git/repos/{repo_id}")
        assert response.status_code == 200  # nosec

        response = client.get(f"/git/repos/{repo_id}")
        assert response.status_code == 404  # nosec

    @pytest.mark.asyncio
    async def test_permissions(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        response = client.post(
            "/git/repos",
            {"name": "perm-repo", "path": _tmp_dir(), "project_id": project_id},
        )
        repo_id = response.json()["id"]

        response = client.post(
            f"/git/repos/{repo_id}/permissions",
            {"user_email": "writer@example.com", "access": "write"},
        )
        assert response.status_code == 200  # nosec
        perm_id = response.json()["id"]

        response = client.get(f"/git/repos/{repo_id}/permissions")
        assert response.status_code == 200  # nosec
        assert response.json()["total"] == 1  # nosec

        response = client.delete(f"/git/repos/{repo_id}/permissions/{perm_id}")
        assert response.status_code == 200  # nosec

        response = client.get(f"/git/repos/{repo_id}/permissions")
        assert response.json()["total"] == 0  # nosec

    @pytest.mark.asyncio
    async def test_hook_access(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        response = client.post(
            "/git/repos",
            {
                "name": "hook-repo",
                "path": _tmp_dir(),
                "project_id": project_id,
                "public": True,
            },
        )
        repo = response.json()
        repo_id = repo["id"]

        # Direct store access used by the shell hook helper.
        repo_model = await GitRepo.objects.get(id=repo_id)
        assert await store.check_access(repo_model, "anonymous@example.com", "read") is True  # nosec
        assert await store.check_access(repo_model, "anonymous@example.com", "write") is False  # nosec

        await store.create_permission(
            repo_model,
            "writer@example.com",
            "write",
        )
        assert await store.check_access(repo_model, "writer@example.com", "write") is True  # nosec

    @pytest.mark.asyncio
    async def test_hook_push_endpoint(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        response = client.post(
            "/git/repos",
            {
                "name": "push-repo",
                "path": _tmp_dir(),
                "project_id": project_id,
                "tests_enabled": False,
            },
        )
        repo_id = response.json()["id"]

        response = client.post(
            f"/git/repos/{repo_id}/hooks/push",
            {
                "ref": "refs/heads/main",
                "old_rev": "0000000000000000000000000000000000000000",
                "new_rev": "a" * 40,
                "pusher_email": "writer@example.com",
            },
        )
        assert response.status_code == 200  # nosec
        data = response.json()
        assert data["ref"] == "refs/heads/main"  # nosec
        assert data["status"] == "completed"  # nosec

        response = client.get(f"/git/repos/{repo_id}/push-log")
        assert response.status_code == 200  # nosec
        assert response.json()["total"] == 1  # nosec

    @pytest.mark.asyncio
    async def test_hooks_script_endpoint(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        response = client.post(
            "/git/repos",
            {"name": "script-repo", "path": _tmp_dir(), "project_id": project_id},
        )
        repo_id = response.json()["id"]

        response = client.get(f"/git/repos/{repo_id}/hooks")
        assert response.status_code == 200  # nosec
        data = response.json()
        assert "pre-receive" in data  # nosec
        assert "update" in data  # nosec
        assert "post-receive" in data  # nosec

    @pytest.mark.asyncio
    async def test_view_endpoints(self, client):
        tmp = _init_temp_repo()
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        response = client.post(
            "/git/repos",
            {"name": "view-repo", "path": tmp.name, "project_id": project_id, "public": True},
        )
        repo_id = response.json()["id"]

        response = client.get(f"/git/repos/{repo_id}/refs")
        assert response.status_code == 200  # nosec
        refs = response.json()
        assert any("main" in ref["name"] for ref in refs)  # nosec

        response = client.get(f"/git/repos/{repo_id}/tree?ref=main")
        assert response.status_code == 200  # nosec
        tree = response.json()
        assert any(entry["name"] == "README.md" for entry in tree)  # nosec

        response = client.get(f"/git/repos/{repo_id}/blob?ref=main&path=README.md")
        assert response.status_code == 200  # nosec
        assert response.json()["content"] == "# Hello\n"  # nosec

        response = client.get(f"/git/repos/{repo_id}/readme?ref=main")
        assert response.status_code == 200  # nosec
        assert response.json()["content"] == "# Hello\n"  # nosec

        response = client.get(f"/git/repos/{repo_id}/commits?ref=main")
        assert response.status_code == 200  # nosec
        assert len(response.json()) == 1  # nosec

    @pytest.mark.asyncio
    async def test_http_clone_public(self, client):
        tmp = _init_temp_repo()
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        client.post(
            "/git/repos",
            {"name": "clone-repo", "path": tmp.name, "project_id": project_id, "public": True},
        )

        tc = TestClient(client.app)
        response = tc.get(
            "http://localhost/git/clone-repo/info/refs?service=git-upload-pack"
        )
        assert response.status_code == 200  # nosec
        assert response.headers["content-type"] == "application/x-git-upload-pack-advertisement"  # nosec
        assert b"# service=git-upload-pack" in response.content  # nosec

        # Stateful RPC request: send an empty request body.
        response = tc.post(
            "http://localhost/git/clone-repo/git-upload-pack",
            content=b"0000",
            headers={"content-type": "application/x-git-upload-pack-request"},
        )
        assert response.status_code == 200  # nosec
        assert response.headers["content-type"] == "application/x-git-upload-pack-result"  # nosec

    @pytest.mark.asyncio
    async def test_http_clone_private_requires_auth(self, client):
        tmp = _init_temp_repo()
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        client.post(
            "/git/repos",
            {"name": "private-clone-repo", "path": tmp.name, "project_id": project_id, "public": False},
        )

        tc = TestClient(client.app)
        response = tc.get(
            "http://localhost/git/private-clone-repo/info/refs?service=git-upload-pack"
        )
        assert response.status_code == 401  # nosec
        assert "WWW-Authenticate" in response.headers  # nosec

    @pytest.mark.asyncio
    async def test_extract_task_refs(self):
        message = "fixes: #1, #2\nrefer: #3"
        refs = git_repo.extract_task_refs(message)
        assert len(refs) == 3  # nosec
        assert {"task_id": 1, "relation": "fix"} in refs  # nosec
        assert {"task_id": 2, "relation": "fix"} in refs  # nosec
        assert {"task_id": 3, "relation": "refer"} in refs  # nosec

    @pytest.mark.asyncio
    async def test_post_receive_records_task_refs(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        # Create a board and column so tasks belong to the repository's project.
        response = client.post(f"/projects/{project_id}/boards", {"name": "board"})
        assert response.status_code == 200  # nosec
        board_id = response.json()["id"]
        response = client.post(f"/boards/{board_id}/columns", {"name": "column"})
        assert response.status_code == 200  # nosec
        column_id = response.json()["id"]
        task_ids = []
        for title in ["Task 1", "Task 2", "Task 3"]:
            response = client.post(f"/columns/{column_id}/tasks", {"title": title})
            assert response.status_code == 200  # nosec
            task_ids.append(response.json()["id"])

        message = f"fixes: #{task_ids[0]}, #{task_ids[1]}\nrefer: #{task_ids[2]}"
        tmp = _init_temp_repo(message=message)

        response = client.post(
            "/git/repos",
            {"name": "task-repo", "path": tmp.name, "project_id": project_id, "public": True},
        )
        repo_id = response.json()["id"]

        proc = subprocess.run(
            ["git", "-C", tmp.name, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )  # nosec
        head = proc.stdout.strip()

        stdin_data = f"0000000000000000000000000000000000000000 {head} refs/heads/main\n"
        with patch("sys.stdin", io.StringIO(stdin_data)):
            result = await post_receive("task-repo")
        assert result == 0  # nosec

        response = client.get(f"/git/repos/{repo_id}/task-refs")
        assert response.status_code == 200  # nosec
        data = response.json()
        assert data["total"] == 3  # nosec
        relations = sorted(r["relation"] for r in data["data"])
        assert relations == ["fix", "fix", "refer"]  # nosec

        response = client.get(f"/git/repos/{repo_id}/commits?ref=main")
        assert response.status_code == 200  # nosec
        commit = response.json()[0]
        assert len(commit["task_refs"]) == 3  # nosec

    @pytest.mark.asyncio
    async def test_post_receive_ignores_task_refs_outside_project(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        repo_project_id = _create_project(client)
        other_project_id = _create_project(client)

        response = client.post(f"/projects/{other_project_id}/boards", {"name": "other-board"})
        assert response.status_code == 200  # nosec
        board_id = response.json()["id"]
        response = client.post(f"/boards/{board_id}/columns", {"name": "other-column"})
        assert response.status_code == 200  # nosec
        column_id = response.json()["id"]
        response = client.post(f"/columns/{column_id}/tasks", {"title": "Other task"})
        assert response.status_code == 200  # nosec
        other_task_id = response.json()["id"]

        message = f"fixes: #{other_task_id}"
        tmp = _init_temp_repo(message=message)

        response = client.post(
            "/git/repos",
            {
                "name": "outside-task-repo",
                "path": tmp.name,
                "project_id": repo_project_id,
                "public": True,
            },
        )
        repo_id = response.json()["id"]

        proc = subprocess.run(
            ["git", "-C", tmp.name, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )  # nosec
        head = proc.stdout.strip()

        stdin_data = f"0000000000000000000000000000000000000000 {head} refs/heads/main\n"
        with patch("sys.stdin", io.StringIO(stdin_data)):
            result = await post_receive("outside-task-repo")
        assert result == 0  # nosec

        response = client.get(f"/git/repos/{repo_id}/task-refs")
        assert response.status_code == 200  # nosec
        assert response.json()["total"] == 0  # nosec

    @pytest.mark.asyncio
    async def test_hook_push_endpoint_sends_webhook(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)

        response = client.post(
            "/git/repos",
            {
                "name": "webhook-repo",
                "path": _tmp_dir(),
                "project_id": project_id,
                "webhook_url": "https://example.com/hook",
            },
        )
        repo_id = response.json()["id"]

        with patch("freenit.api.git.notify_push") as mock_notify:
            response = client.post(
                f"/git/repos/{repo_id}/hooks/push",
                {
                    "ref": "refs/heads/main",
                    "old_rev": "0000000000000000000000000000000000000000",
                    "new_rev": "a" * 40,
                    "pusher_email": "pusher@example.com",
                },
            )
        assert response.status_code == 200  # nosec
        mock_notify.assert_awaited_once()
        args = mock_notify.await_args.args
        assert args[0].id == repo_id  # nosec
        assert args[1] == "refs/heads/main"  # nosec

    @pytest.mark.asyncio
    async def test_post_receive_sends_webhook(self, client):
        admin: User = factories.User(admin=True)
        await admin.save()
        client.login(user=admin)
        project_id = _create_project(client)
        tmp = _init_temp_repo()

        response = client.post(
            "/git/repos",
            {
                "name": "post-webhook-repo",
                "path": tmp.name,
                "project_id": project_id,
                "webhook_url": "https://example.com/hook",
            },
        )
        repo_id = response.json()["id"]

        proc = subprocess.run(
            ["git", "-C", tmp.name, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )  # nosec
        head = proc.stdout.strip()

        stdin_data = f"0000000000000000000000000000000000000000 {head} refs/heads/main\n"
        with patch("freenit.git.hooks.notify_push") as mock_notify:
            with patch("sys.stdin", io.StringIO(stdin_data)):
                result = await post_receive("post-webhook-repo")
        assert result == 0  # nosec
        mock_notify.assert_awaited_once()
        args = mock_notify.await_args.args
        assert args[0].id == repo_id  # nosec
        assert args[1] == "refs/heads/main"  # nosec

    @pytest.mark.asyncio
    async def test_webhook_payload(self):
        from freenit.git.webhook import notify_push

        repo = AsyncMock()
        repo.id = 1
        repo.name = "payload-repo"
        repo.path = None
        repo.webhook_url = "https://example.com/hook"

        from unittest.mock import Mock

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("freenit.git.webhook.httpx.AsyncClient", return_value=mock_client):
            await notify_push(
                repo,
                "refs/heads/main",
                "0" * 40,
                "a" * 40,
                "pusher@example.com",
            )

        mock_client.post.assert_awaited_once()
        url, kwargs = mock_client.post.await_args.args, mock_client.post.await_args.kwargs
        assert url[0] == "https://example.com/hook"  # nosec
        payload = kwargs["json"]
        assert payload["event"] == "push"  # nosec
        assert payload["repository"]["name"] == "payload-repo"  # nosec
        assert payload["ref"] == "refs/heads/main"  # nosec
        assert payload["pusher"]["email"] == "pusher@example.com"  # nosec
