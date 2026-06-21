from datetime import datetime

from fastapi import HTTPException

from freenit.models.git import (
    GitCommitTaskRef,
    GitPermission,
    GitPushLog,
    GitRepo,
    IntegrityError,
    NotFoundError,
)
from freenit.models.pagination import Page, paginate
from .tasks import task_in_project


_ACCESS_LEVELS = {
    "read": 0,
    "write": 1,
    "admin": 2,
}


async def get_repo(id: int) -> GitRepo:
    try:
        return await GitRepo.objects.get(id=id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No such repository")


async def get_repo_by_name(name: str) -> GitRepo:
    try:
        return await GitRepo.objects.get(name=name)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No such repository")


async def list_repos(
    page: int,
    perpage: int,
    public: bool | None = None,
) -> Page[GitRepo]:
    query = GitRepo.objects
    if public is not None:
        query = query.filter(public=public)
    return await paginate(query.order_by("-created_at"), page, perpage)


async def count_repos_by_name_or_path(name: str, path: str) -> int:
    name_count = await GitRepo.objects.filter(name=name).count()
    path_count = await GitRepo.objects.filter(path=path).count()
    return name_count + path_count


async def create_repo(**kwargs) -> GitRepo:
    try:
        return await GitRepo.objects.create(**kwargs)
    except IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Repository already exists: {e}")


async def update_repo(repo: GitRepo, data) -> GitRepo:
    await repo.patch(data)
    return repo


async def delete_repo(repo: GitRepo) -> None:
    await repo.delete()


async def list_permissions(
    repo_id: int,
    page: int,
    perpage: int,
) -> Page[GitPermission]:
    return await paginate(
        GitPermission.objects.filter(repo_id=repo_id).order_by("-created_at"),
        page,
        perpage,
    )


async def get_permission(id: int) -> GitPermission:
    try:
        return await GitPermission.objects.get(id=id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No such permission")


async def create_permission(repo: GitRepo, user_email: str, access: str) -> GitPermission:
    if access not in _ACCESS_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid access level")
    try:
        return await GitPermission.objects.create(
            repo=repo,
            repo_id=repo.id,
            user_email=user_email,
            access=access,
            created_at=datetime.utcnow(),
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=409, detail=f"Permission already exists: {e}"
        )


async def delete_permission(permission: GitPermission) -> None:
    await permission.delete()


async def check_access(
    repo: GitRepo,
    user_email: str,
    required: str,
) -> bool:
    required_level = _ACCESS_LEVELS.get(required)
    if required_level is None:
        return False
    if required == "read" and repo.public:
        return True
    try:
        permission = await GitPermission.objects.filter(
            repo_id=repo.id,
            user_email=user_email,
        ).get()
    except NotFoundError:
        return False
    return _ACCESS_LEVELS.get(permission.access, -1) >= required_level


async def list_push_logs(
    repo_id: int,
    page: int,
    perpage: int,
) -> Page[GitPushLog]:
    return await paginate(
        GitPushLog.objects.filter(repo_id=repo_id).order_by("-created_at"),
        page,
        perpage,
    )


async def get_push_log(id: int) -> GitPushLog:
    try:
        return await GitPushLog.objects.get(id=id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No such push log")


async def create_push_log(
    repo: GitRepo,
    ref: str,
    old_rev: str | None,
    new_rev: str | None,
    pusher_email: str,
    status: str = "pending",
    output: str | None = None,
) -> GitPushLog:
    now = datetime.utcnow()
    return await GitPushLog.objects.create(
        repo=repo,
        repo_id=repo.id,
        ref=ref,
        old_rev=old_rev,
        new_rev=new_rev,
        pusher_email=pusher_email,
        status=status,
        output=output,
        created_at=now,
        updated_at=now,
    )


async def update_push_status(
    push_log: GitPushLog,
    status: str,
    output: str | None = None,
) -> GitPushLog:
    push_log.status = status
    push_log.output = output
    push_log.updated_at = datetime.utcnow()
    await push_log.save(update_fields={"status", "output", "updated_at"})
    return push_log


async def create_commit_task_ref(
    repo: GitRepo,
    task_id: int,
    commit_sha: str,
    relation: str,
) -> GitCommitTaskRef:
    if not await task_in_project(task_id, repo.project_id):
        raise HTTPException(
            status_code=400, detail="Task does not belong to repository project"
        )
    try:
        return await GitCommitTaskRef.objects.create(
            repo=repo,
            repo_id=repo.id,
            task_id=task_id,
            commit_sha=commit_sha,
            relation=relation,
            created_at=datetime.utcnow(),
        )
    except IntegrityError:
        # Already recorded; return the existing one.
        return await GitCommitTaskRef.objects.filter(
            repo_id=repo.id,
            task_id=task_id,
            commit_sha=commit_sha,
            relation=relation,
        ).get()


async def list_commit_task_refs(
    repo_id: int,
    page: int,
    perpage: int,
) -> Page[GitCommitTaskRef]:
    return await paginate(
        GitCommitTaskRef.objects.filter(repo_id=repo_id).order_by("-created_at"),
        page,
        perpage,
    )


async def list_commit_task_refs_by_commit(
    repo_id: int,
    commit_sha: str,
) -> list[GitCommitTaskRef]:
    return await GitCommitTaskRef.objects.filter(
        repo_id=repo_id,
        commit_sha=commit_sha,
    ).all()


async def list_commit_task_refs_by_task(
    repo_id: int,
    task_id: int,
    page: int,
    perpage: int,
) -> Page[GitCommitTaskRef]:
    return await paginate(
        GitCommitTaskRef.objects.filter(
            repo_id=repo_id,
            task_id=task_id,
        ).order_by("-created_at"),
        page,
        perpage,
    )


async def get_commit_task_ref_map(repo_id: int) -> dict[str, list[dict]]:
    refs = await GitCommitTaskRef.objects.filter(repo_id=repo_id).all()
    result: dict[str, list[dict]] = {}
    for ref in refs:
        result.setdefault(ref.commit_sha, []).append({
            "task_id": ref.task_id,
            "relation": ref.relation,
        })
    return result
