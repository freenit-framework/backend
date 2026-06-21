import asyncio
import logging
import shlex
import subprocess  # nosec: B404
from datetime import datetime
import pydantic
from fastapi import BackgroundTasks, Depends, Header, HTTPException

from freenit.api.router import route
from freenit.config import getConfig
from freenit.decorators import description
from freenit.git import repo as git_repo
from freenit.git import store
from freenit.models.git import GitPermission, GitPushLog, GitRepo
from freenit.models.pagination import Page
from freenit.models.user import User
from freenit.permissions import git_perms

config = getConfig()
log = logging.getLogger("git")

tags = ["git"]


def _current_user(user=Depends(git_perms)):
    return user


def _require_admin(cur_user: User) -> None:
    if not cur_user.admin:
        raise HTTPException(status_code=403, detail="Only admin users can perform this action")


class GitRepoCreate(pydantic.BaseModel):
    name: str
    path: str
    project_id: int
    description: str | None = None
    public: bool = False
    default_branch: str = "main"
    tests_enabled: bool = False
    test_command: str | None = None


class GitRepoUpdate(pydantic.BaseModel):
    name: str | None = None
    path: str | None = None
    project_id: int | None = None
    description: str | None = None
    public: bool | None = None
    default_branch: str | None = None
    tests_enabled: bool | None = None
    test_command: str | None = None


class GitRepoResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    path: str
    description: str | None = None
    public: bool
    default_branch: str
    tests_enabled: bool
    test_command: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GitPermissionCreate(pydantic.BaseModel):
    user_email: pydantic.EmailStr
    access: str


class GitPermissionResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    repo_id: int
    user_email: str
    access: str
    created_at: datetime | None = None


class GitPushLogResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    repo_id: int
    ref: str
    old_rev: str | None = None
    new_rev: str | None = None
    pusher_email: str
    status: str
    output: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HookPushInput(pydantic.BaseModel):
    ref: str
    old_rev: str | None = None
    new_rev: str | None = None
    pusher_email: pydantic.EmailStr


async def _get_repo(id: int) -> GitRepo:
    return await store.get_repo(id)


async def _get_permission(perm_id: int) -> GitPermission:
    return await store.get_permission(perm_id)


async def _run_tests(repo: GitRepo, push_log: GitPushLog) -> None:
    command = repo.test_command
    if not command:
        return
    try:
        log.info("Running tests for repo %s: %s", repo.name, command)
        proc = await asyncio.to_thread(
            subprocess.run,
            shlex.split(command),
            capture_output=True,
            text=True,
            cwd=repo.path or None,
            check=False,
        )  # nosec
        output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}".strip()
        status = "success" if proc.returncode == 0 else "failure"
    except Exception as exc:
        log.error("Failed to run tests for repo %s: %s", repo.name, exc)
        output = str(exc)
        status = "failure"
    await store.update_push_status(push_log, status, output)


@route("/git/repos", tags=tags)
class GitRepoListAPI:
    @staticmethod
    @description("Get repositories")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        cur_user: User = Depends(git_perms),
    ) -> Page[GitRepoResponse]:
        _require_admin(cur_user)
        return await store.list_repos(page, perpage)

    @staticmethod
    @description("Create repository")
    async def post(
        data: GitRepoCreate,
        cur_user: User = Depends(git_perms),
    ) -> GitRepoResponse:
        _require_admin(cur_user)
        if "/" in data.name or data.name.startswith("."):
            raise HTTPException(status_code=400, detail="Invalid repository name")
        existing = await store.count_repos_by_name_or_path(data.name, data.path)
        if existing > 0:
            raise HTTPException(status_code=409, detail="Repository name or path already in use")
        now = datetime.utcnow()
        repo = await store.create_repo(
            name=data.name,
            path=data.path,
            project_id=data.project_id,
            description=data.description,
            public=data.public,
            default_branch=data.default_branch,
            tests_enabled=data.tests_enabled,
            test_command=data.test_command,
            created_at=now,
            updated_at=now,
        )
        return GitRepoResponse.model_validate(repo)


@route("/git/repos/public", tags=tags)
class GitRepoPublicAPI:
    @staticmethod
    @description("Get public repositories")
    async def get(
        page: int = Header(default=1),
        perpage: int = Header(default=10),
    ) -> Page[GitRepoResponse]:
        return await store.list_repos(page, perpage, public=True)


@route("/git/repos/{id}", tags=tags)
class GitRepoDetailAPI:
    @staticmethod
    async def get(
        id: int,
        cur_user: User = Depends(git_perms),
    ) -> GitRepoResponse:
        _require_admin(cur_user)
        repo = await _get_repo(id)
        return GitRepoResponse.model_validate(repo)

    @staticmethod
    async def patch(
        id: int,
        data: GitRepoUpdate,
        cur_user: User = Depends(git_perms),
    ) -> GitRepoResponse:
        _require_admin(cur_user)
        repo = await _get_repo(id)
        await store.update_repo(repo, data)
        return GitRepoResponse.model_validate(repo)

    @staticmethod
    async def delete(
        id: int,
        cur_user: User = Depends(git_perms),
    ) -> GitRepoResponse:
        _require_admin(cur_user)
        repo = await _get_repo(id)
        await store.delete_repo(repo)
        return GitRepoResponse.model_validate(repo)


@route("/git/repos/{id}/permissions", tags=tags)
class GitPermissionListAPI:
    @staticmethod
    @description("List repository permissions")
    async def get(
        id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        cur_user: User = Depends(git_perms),
    ) -> Page[GitPermissionResponse]:
        _require_admin(cur_user)
        await _get_repo(id)
        return await store.list_permissions(id, page, perpage)

    @staticmethod
    @description("Add repository permission")
    async def post(
        id: int,
        data: GitPermissionCreate,
        cur_user: User = Depends(git_perms),
    ) -> GitPermissionResponse:
        _require_admin(cur_user)
        repo = await _get_repo(id)
        permission = await store.create_permission(
            repo=repo,
            user_email=data.user_email,
            access=data.access,
        )
        return GitPermissionResponse.model_validate(permission)


@route("/git/repos/{id}/permissions/{perm_id}", tags=tags)
class GitPermissionDetailAPI:
    @staticmethod
    @description("Remove repository permission")
    async def delete(
        id: int,
        perm_id: int,
        cur_user: User = Depends(git_perms),
    ) -> GitPermissionResponse:
        _require_admin(cur_user)
        await _get_repo(id)
        permission = await _get_permission(perm_id)
        if permission.repo_id != id:
            raise HTTPException(status_code=404, detail="Permission not found")
        await store.delete_permission(permission)
        return GitPermissionResponse.model_validate(permission)


@route("/git/repos/{id}/push-log", tags=tags)
class GitPushLogListAPI:
    @staticmethod
    @description("List push log")
    async def get(
        id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=10),
        cur_user: User = Depends(git_perms),
    ) -> Page[GitPushLogResponse]:
        _require_admin(cur_user)
        await _get_repo(id)
        return await store.list_push_logs(id, page, perpage)


@route("/git/repos/{id}/hooks/push", tags=tags)
class GitHookPushAPI:
    @staticmethod
    @description("Record a push and optionally trigger tests")
    async def post(
        id: int,
        data: HookPushInput,
        background_tasks: BackgroundTasks,
    ) -> GitPushLogResponse:
        repo = await _get_repo(id)
        push_log = await store.create_push_log(
            repo=repo,
            ref=data.ref,
            old_rev=data.old_rev,
            new_rev=data.new_rev,
            pusher_email=data.pusher_email,
            status="pending",
        )
        if repo.tests_enabled and repo.test_command:
            background_tasks.add_task(_run_tests, repo, push_log)
        else:
            await store.update_push_status(push_log, "completed")
        return GitPushLogResponse.model_validate(push_log)


@route("/git/repos/{id}/hooks", tags=tags)
class GitHooksAPI:
    @staticmethod
    @description("Get hook scripts for this repository")
    async def get(
        id: int,
        cur_user: User = Depends(git_perms),
    ) -> dict[str, str]:
        _require_admin(cur_user)
        repo = await _get_repo(id)
        return {
            "pre-receive": (
                "#!/bin/sh\n"
                f"python -m freenit.git.hooks '{repo.name}' pre-receive\n"
            ),
            "update": (
                "#!/bin/sh\n"
                "ref=$1\n"
                "oldrev=$2\n"
                "newrev=$3\n"
                f"python -m freenit.git.hooks '{repo.name}' update \"$ref\" \"$oldrev\" \"$newrev\"\n"
            ),
            "post-receive": (
                "#!/bin/sh\n"
                f"python -m freenit.git.hooks '{repo.name}' post-receive\n"
            ),
        }


class GitRefResponse(pydantic.BaseModel):
    name: str
    sha: str


class GitCommitTaskRefItem(pydantic.BaseModel):
    task_id: int
    relation: str


class GitCommitResponse(pydantic.BaseModel):
    sha: str
    message: str
    author: str
    committer: str
    timestamp: datetime | None = None
    task_refs: list[GitCommitTaskRefItem] = []


class GitTreeEntryResponse(pydantic.BaseModel):
    name: str
    mode: str
    type: str
    sha: str


class GitBlobResponse(pydantic.BaseModel):
    name: str
    sha: str
    size: int
    content: str
    binary: bool


class GitReadmeResponse(pydantic.BaseModel):
    name: str
    sha: str
    content: str
    binary: bool


@route("/git/repos/{id}/refs", tags=tags)
class GitRefsAPI:
    @staticmethod
    @description("List branches and tags")
    async def get(
        id: int,
        cur_user: User = Depends(git_perms),
    ) -> list[GitRefResponse]:
        repo = await _get_repo(id)
        if not repo.public:
            _require_admin(cur_user)
        return [
            GitRefResponse.model_validate(item)
            for item in git_repo.list_refs(repo.path)
        ]


@route("/git/repos/{id}/commits", tags=tags)
class GitCommitsAPI:
    @staticmethod
    @description("List commits")
    async def get(
        id: int,
        ref: str = "main",
        page: int = Header(default=1),
        perpage: int = Header(default=20),
        cur_user: User = Depends(git_perms),
    ) -> list[GitCommitResponse]:
        repo = await _get_repo(id)
        if not repo.public:
            _require_admin(cur_user)
        commits = git_repo.list_commits(repo.path, ref, page, perpage)
        task_ref_map = await store.get_commit_task_ref_map(id)
        result = []
        for commit in commits:
            data = dict(commit)
            data["task_refs"] = task_ref_map.get(commit["sha"], [])
            result.append(GitCommitResponse.model_validate(data))
        return result


@route("/git/repos/{id}/tree", tags=tags)
class GitTreeAPI:
    @staticmethod
    @description("List tree entries")
    async def get(
        id: int,
        ref: str = "main",
        path: str = "",
        cur_user: User = Depends(git_perms),
    ) -> list[GitTreeEntryResponse]:
        repo = await _get_repo(id)
        if not repo.public:
            _require_admin(cur_user)
        return [
            GitTreeEntryResponse.model_validate(item)
            for item in git_repo.list_tree(repo.path, ref, path)
        ]


@route("/git/repos/{id}/blob", tags=tags)
class GitBlobAPI:
    @staticmethod
    @description("Get file content")
    async def get(
        id: int,
        ref: str = "main",
        path: str = "",
        cur_user: User = Depends(git_perms),
    ) -> GitBlobResponse:
        repo = await _get_repo(id)
        if not repo.public:
            _require_admin(cur_user)
        if not path:
            raise HTTPException(status_code=400, detail="Path is required")
        return GitBlobResponse.model_validate(
            git_repo.get_blob(repo.path, ref, path)
        )


@route("/git/repos/{id}/readme", tags=tags)
class GitReadmeAPI:
    @staticmethod
    @description("Get README content")
    async def get(
        id: int,
        ref: str = "main",
        cur_user: User = Depends(git_perms),
    ) -> GitReadmeResponse:
        repo = await _get_repo(id)
        if not repo.public:
            _require_admin(cur_user)
        data = git_repo.get_readme(repo.path, ref)
        if data is None:
            raise HTTPException(status_code=404, detail="README not found")
        return GitReadmeResponse.model_validate(data)


@route("/git/repos/{id}/clone-url", tags=tags)
class GitCloneUrlAPI:
    @staticmethod
    @description("Get HTTPS clone URL")
    async def get(
        id: int,
        cur_user: User = Depends(git_perms),
    ) -> dict[str, str]:
        repo = await _get_repo(id)
        if not repo.public:
            _require_admin(cur_user)
        host = config.hostname
        if config.port != 443 and config.port != 80:
            host = f"{host}:{config.port}"
        return {"clone_url": f"https://{host}/git/{repo.name}"}


class GitCommitTaskRefResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    repo_id: int
    task_id: int
    commit_sha: str
    relation: str
    created_at: datetime | None = None


@route("/git/repos/{id}/task-refs", tags=tags)
class GitCommitTaskRefListAPI:
    @staticmethod
    @description("List commit-task references")
    async def get(
        id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=20),
        cur_user: User = Depends(git_perms),
    ) -> Page[GitCommitTaskRefResponse]:
        repo = await _get_repo(id)
        if not repo.public:
            _require_admin(cur_user)
        return await store.list_commit_task_refs(id, page, perpage)


@route("/git/repos/{id}/task-refs/by-task/{task_id}", tags=tags)
class GitCommitTaskRefByTaskAPI:
    @staticmethod
    @description("List commit-task references for a task")
    async def get(
        id: int,
        task_id: int,
        page: int = Header(default=1),
        perpage: int = Header(default=20),
        cur_user: User = Depends(git_perms),
    ) -> Page[GitCommitTaskRefResponse]:
        repo = await _get_repo(id)
        if not repo.public:
            _require_admin(cur_user)
        return await store.list_commit_task_refs_by_task(id, task_id, page, perpage)
