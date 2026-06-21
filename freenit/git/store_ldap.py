from __future__ import annotations

from datetime import datetime, timezone
from math import ceil

from bonsai import LDAPEntry, LDAPSearchScope, errors
from fastapi import HTTPException

from freenit.config import getConfig
from freenit.models.git import GitCommitTaskRef, GitPermission, GitPushLog, GitRepo
from freenit.models.ldap.base import class2filter, get_client, next_git_id, save_data
from freenit.models.pagination import Page
from .tasks import task_in_project

config = getConfig()

_ACCESS_LEVELS = {
    "read": 0,
    "write": 1,
    "admin": 2,
}


def _first(entry, attr, default=None):
    value = entry.get(attr)
    if not value:
        return default
    if isinstance(value, (list, tuple)):
        value = value[0]
    return value


def _int(entry, attr, default=None):
    value = _first(entry, attr)
    if value is None:
        return default
    return int(value)


def _ldap_dt(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y%m%d%H%M%SZ")


def _ldap_bool(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def _repo_dn(name: str) -> str:
    return config.ldap.gitRepoDN.format(name)


def _permission_dn(repo_name: str, perm_id: int) -> str:
    return f"cn={perm_id},{_repo_dn(repo_name)}"


def _push_log_dn(repo_name: str, log_id: int) -> str:
    return f"cn={log_id},{_repo_dn(repo_name)}"


def _repo_filter():
    return class2filter(config.ldap.gitRepoClasses)


def _permission_filter():
    return class2filter(config.ldap.gitPermissionClasses)


def _push_log_filter():
    return class2filter(config.ldap.gitPushLogClasses)


def _task_ref_filter():
    return class2filter(config.ldap.gitCommitTaskRefClasses)


def _task_ref_dn(repo_name: str, ref_id: int) -> str:
    return f"cn={ref_id},{_repo_dn(repo_name)}"


async def _search_repo_by_id(repo_id: int):
    classes = _repo_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.gitBase,
            LDAPSearchScope.SUB,
            f"(&{classes}(gitIdNumber={repo_id}))",
        )
    if len(res) < 1:
        raise HTTPException(status_code=404, detail="No such repository")
    if len(res) > 1:
        raise HTTPException(status_code=409, detail="Multiple repositories found")
    return res[0]


async def _search_repo_by_name(name: str):
    classes = _repo_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.gitBase,
            LDAPSearchScope.SUB,
            f"(&{classes}(cn={name}))",
        )
    return res[0] if res else None


async def _count_by_name_or_path(name: str, path: str) -> int:
    classes = _repo_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.gitBase,
            LDAPSearchScope.SUB,
            f"(&{classes}(|(cn={name})(gitPath={path})))",
        )
    return len(res)


async def get_repo(id: int) -> GitRepo:
    entry = await _search_repo_by_id(id)
    return GitRepo.from_entry(entry)


async def get_repo_by_name(name: str) -> GitRepo:
    entry = await _search_repo_by_name(name)
    if entry is None:
        raise HTTPException(status_code=404, detail="No such repository")
    return GitRepo.from_entry(entry)


async def list_repos(
    page: int,
    perpage: int,
    public: bool | None = None,
) -> Page[GitRepo]:
    classes = _repo_filter()
    filter_exp = classes
    if public is not None:
        filter_exp = f"(&{classes}(gitPublic={_ldap_bool(public)}))"
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.gitBase,
            LDAPSearchScope.SUB,
            filter_exp,
        )
    data = [GitRepo.from_entry(entry) for entry in res]
    data.sort(key=lambda r: r.id, reverse=True)
    total = len(data)
    pages = ceil(total / perpage) if perpage else 1
    if total > 0 and page > pages:
        raise HTTPException(status_code=404, detail="No such page")
    offset = max(page - 1, 0) * perpage
    page_data = data[offset : offset + perpage]
    return Page(total=total, page=page, pages=pages, perpage=perpage, data=page_data)


async def count_repos_by_name_or_path(name: str, path: str) -> int:
    return await _count_by_name_or_path(name, path)


async def create_repo(**kwargs) -> GitRepo:
    name = kwargs["name"]
    path = kwargs["path"]
    project_id = kwargs.get("project_id")
    if project_id is None:
        raise HTTPException(status_code=400, detail="project_id is required")

    existing = await _search_repo_by_name(name)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Repository already exists")

    if await _count_by_name_or_path(name, path) > 0:
        raise HTTPException(
            status_code=409, detail="Repository name or path already in use"
        )

    repo_id = await next_git_id()
    now = kwargs.get("created_at") or datetime.utcnow()
    dn = _repo_dn(name)
    entry = LDAPEntry(dn)
    entry["objectClass"] = config.ldap.gitRepoClasses
    entry["cn"] = name
    entry["gitIdNumber"] = repo_id
    entry["gitProjectId"] = project_id
    entry["gitPath"] = path
    description = kwargs.get("description")
    if description:
        entry["description"] = description
    entry["gitPublic"] = _ldap_bool(kwargs.get("public", False))
    entry["gitDefaultBranch"] = kwargs.get("default_branch", "main")
    entry["gitTestsEnabled"] = _ldap_bool(kwargs.get("tests_enabled", False))
    test_command = kwargs.get("test_command")
    if test_command:
        entry["gitTestCommand"] = test_command
    entry["createdAt"] = _ldap_dt(now)
    entry["updatedAt"] = _ldap_dt(now)

    try:
        await save_data(entry)
    except errors.AlreadyExists:
        raise HTTPException(status_code=409, detail="Repository already exists")

    return GitRepo(
        dn=dn,
        id=repo_id,
        project_id=project_id,
        name=name,
        path=path,
        description=description,
        public=kwargs.get("public", False),
        default_branch=kwargs.get("default_branch", "main"),
        tests_enabled=kwargs.get("tests_enabled", False),
        test_command=test_command,
        created_at=now,
        updated_at=now,
    )


async def update_repo(repo: GitRepo, data) -> GitRepo:
    fields = data.model_dump(exclude_none=True)
    if not fields:
        return repo

    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(repo.dn, LDAPSearchScope.BASE)
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such repository")
        entry = res[0]

        if "name" in fields:
            entry["cn"] = fields["name"]
        if "path" in fields:
            entry["gitPath"] = fields["path"]
        if "project_id" in fields:
            entry["gitProjectId"] = fields["project_id"]
        if "description" in fields:
            entry["description"] = fields["description"] or []
        if "public" in fields:
            entry["gitPublic"] = _ldap_bool(fields["public"])
        if "default_branch" in fields:
            entry["gitDefaultBranch"] = fields["default_branch"]
        if "tests_enabled" in fields:
            entry["gitTestsEnabled"] = _ldap_bool(fields["tests_enabled"])
        if "test_command" in fields:
            value = fields["test_command"]
            if value:
                entry["gitTestCommand"] = value
            elif "gitTestCommand" in entry:
                del entry["gitTestCommand"]
        entry["updatedAt"] = _ldap_dt(datetime.utcnow())
        await entry.modify()

    for key, value in fields.items():
        setattr(repo, key, value)
    repo.updated_at = datetime.utcnow()
    return repo


async def delete_repo(repo: GitRepo) -> None:
    client = get_client()
    async with client.connect(is_async=True) as conn:
        children = await conn.search(
            repo.dn,
            LDAPSearchScope.SUB,
            "(objectClass=*)",
            attrlist=["objectClass"],
        )
        for child in children:
            child_dn = str(child["dn"])
            if child_dn != repo.dn:
                await child.delete()
        res = await conn.search(repo.dn, LDAPSearchScope.BASE)
        if res:
            await res[0].delete()


async def list_permissions(
    repo_id: int,
    page: int,
    perpage: int,
) -> Page[GitPermission]:
    repo_entry = await _search_repo_by_id(repo_id)
    repo_name = str(repo_entry["cn"][0])
    classes = _permission_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _repo_dn(repo_name),
            LDAPSearchScope.ONELEVEL,
            classes,
        )
    data = [GitPermission.from_entry(entry, repo_id) for entry in res]
    data.sort(key=lambda p: p.id, reverse=True)
    total = len(data)
    pages = ceil(total / perpage) if perpage else 1
    if total > 0 and page > pages:
        raise HTTPException(status_code=404, detail="No such page")
    offset = max(page - 1, 0) * perpage
    page_data = data[offset : offset + perpage]
    return Page(total=total, page=page, pages=pages, perpage=perpage, data=page_data)


async def get_permission(id: int) -> GitPermission:
    classes = _permission_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.gitBase,
            LDAPSearchScope.SUB,
            f"(&{classes}(gitIdNumber={id}))",
        )
    if len(res) < 1:
        raise HTTPException(status_code=404, detail="No such permission")
    repo_id = 0
    repo_dn = str(res[0]["dn"]).split(",", 1)[1]
    repo_res = await _search_repo_by_dn(repo_dn)
    if repo_res:
        repo_id = _int(repo_res, "gitIdNumber", 0)
    return GitPermission.from_entry(res[0], repo_id)


async def _search_repo_by_dn(dn: str):
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(dn, LDAPSearchScope.BASE)
    return res[0] if res else None


async def create_permission(repo: GitRepo, user_email: str, access: str) -> GitPermission:
    if access not in _ACCESS_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid access level")
    perm_id = await next_git_id()
    created_at = datetime.utcnow()
    dn = _permission_dn(repo.name, perm_id)
    entry = LDAPEntry(dn)
    entry["objectClass"] = config.ldap.gitPermissionClasses
    entry["cn"] = str(perm_id)
    entry["gitIdNumber"] = perm_id
    entry["mail"] = user_email
    entry["gitAccess"] = access
    entry["createdAt"] = _ldap_dt(created_at)
    try:
        await save_data(entry)
    except errors.AlreadyExists:
        raise HTTPException(status_code=409, detail="Permission already exists")
    return GitPermission(
        dn=dn,
        id=perm_id,
        repo_id=repo.id,
        user_email=user_email,
        access=access,
        created_at=created_at,
    )


async def delete_permission(permission: GitPermission) -> None:
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(permission.dn, LDAPSearchScope.BASE)
        if res:
            await res[0].delete()


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
    classes = _permission_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _repo_dn(repo.name),
            LDAPSearchScope.ONELEVEL,
            f"(&{classes}(mail={user_email}))",
        )
    if not res:
        return False
    access = _first(res[0], "gitAccess", "read")
    return _ACCESS_LEVELS.get(access, -1) >= required_level


async def list_push_logs(
    repo_id: int,
    page: int,
    perpage: int,
) -> Page[GitPushLog]:
    repo_entry = await _search_repo_by_id(repo_id)
    repo_name = str(repo_entry["cn"][0])
    classes = _push_log_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _repo_dn(repo_name),
            LDAPSearchScope.ONELEVEL,
            classes,
        )
    data = [GitPushLog.from_entry(entry, repo_id) for entry in res]
    data.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    total = len(data)
    pages = ceil(total / perpage) if perpage else 1
    if total > 0 and page > pages:
        raise HTTPException(status_code=404, detail="No such page")
    offset = max(page - 1, 0) * perpage
    page_data = data[offset : offset + perpage]
    return Page(total=total, page=page, pages=pages, perpage=perpage, data=page_data)


async def get_push_log(id: int) -> GitPushLog:
    classes = _push_log_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            config.ldap.gitBase,
            LDAPSearchScope.SUB,
            f"(&{classes}(gitIdNumber={id}))",
        )
    if len(res) < 1:
        raise HTTPException(status_code=404, detail="No such push log")
    repo_id = 0
    repo_dn = str(res[0]["dn"]).split(",", 1)[1]
    repo_res = await _search_repo_by_dn(repo_dn)
    if repo_res:
        repo_id = _int(repo_res, "gitIdNumber", 0)
    return GitPushLog.from_entry(res[0], repo_id)


async def create_push_log(
    repo: GitRepo,
    ref: str,
    old_rev: str | None,
    new_rev: str | None,
    pusher_email: str,
    status: str = "pending",
    output: str | None = None,
) -> GitPushLog:
    log_id = await next_git_id()
    now = datetime.utcnow()
    dn = _push_log_dn(repo.name, log_id)
    entry = LDAPEntry(dn)
    entry["objectClass"] = config.ldap.gitPushLogClasses
    entry["cn"] = str(log_id)
    entry["gitIdNumber"] = log_id
    entry["gitRef"] = ref
    if old_rev:
        entry["gitOldRev"] = old_rev
    if new_rev:
        entry["gitNewRev"] = new_rev
    entry["gitPusherEmail"] = pusher_email
    entry["gitStatus"] = status
    if output:
        entry["gitOutput"] = output
    entry["createdAt"] = _ldap_dt(now)
    entry["updatedAt"] = _ldap_dt(now)
    await save_data(entry)
    return GitPushLog(
        dn=dn,
        id=log_id,
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
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(push_log.dn, LDAPSearchScope.BASE)
        if len(res) < 1:
            raise HTTPException(status_code=404, detail="No such push log")
        entry = res[0]
        entry["gitStatus"] = status
        if output is None:
            if "gitOutput" in entry:
                del entry["gitOutput"]
        else:
            entry["gitOutput"] = output
        entry["updatedAt"] = _ldap_dt(datetime.utcnow())
        await entry.modify()
    push_log.status = status
    push_log.output = output
    push_log.updated_at = datetime.utcnow()
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
    list_entry = await _search_repo_by_id(repo.id)
    repo_name = str(list_entry["cn"][0])
    ref_id = await next_git_id()
    created_at = datetime.utcnow()
    dn = _task_ref_dn(repo_name, ref_id)
    entry = LDAPEntry(dn)
    entry["objectClass"] = config.ldap.gitCommitTaskRefClasses
    entry["cn"] = str(ref_id)
    entry["gitIdNumber"] = ref_id
    entry["gitTaskId"] = task_id
    entry["gitCommitSha"] = commit_sha
    entry["gitRelation"] = relation
    entry["createdAt"] = _ldap_dt(created_at)
    try:
        await save_data(entry)
    except errors.AlreadyExists:
        existing = await _search_task_ref(repo_name, task_id, commit_sha, relation)
        return GitCommitTaskRef.from_entry(existing, repo.id)
    return GitCommitTaskRef(
        dn=dn,
        id=ref_id,
        repo_id=repo.id,
        task_id=task_id,
        commit_sha=commit_sha,
        relation=relation,
        created_at=created_at,
    )


async def _search_task_ref(repo_name: str, task_id: int, commit_sha: str, relation: str):
    classes = _task_ref_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _repo_dn(repo_name),
            LDAPSearchScope.ONELEVEL,
            f"(&{classes}(gitTaskId={task_id})(gitCommitSha={commit_sha})(gitRelation={relation}))",
        )
    if not res:
        raise HTTPException(status_code=404, detail="Task reference not found")
    return res[0]


async def list_commit_task_refs(
    repo_id: int,
    page: int,
    perpage: int,
) -> Page[GitCommitTaskRef]:
    repo_entry = await _search_repo_by_id(repo_id)
    repo_name = str(repo_entry["cn"][0])
    classes = _task_ref_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _repo_dn(repo_name),
            LDAPSearchScope.ONELEVEL,
            classes,
        )
    data = [GitCommitTaskRef.from_entry(entry, repo_id) for entry in res]
    data.sort(key=lambda r: r.created_at or datetime.min, reverse=True)
    total = len(data)
    pages = ceil(total / perpage) if perpage else 1
    if total > 0 and page > pages:
        raise HTTPException(status_code=404, detail="No such page")
    offset = max(page - 1, 0) * perpage
    page_data = data[offset : offset + perpage]
    return Page(total=total, page=page, pages=pages, perpage=perpage, data=page_data)


async def list_commit_task_refs_by_commit(
    repo_id: int,
    commit_sha: str,
) -> list[GitCommitTaskRef]:
    repo_entry = await _search_repo_by_id(repo_id)
    repo_name = str(repo_entry["cn"][0])
    classes = _task_ref_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _repo_dn(repo_name),
            LDAPSearchScope.ONELEVEL,
            f"(&{classes}(gitCommitSha={commit_sha}))",
        )
    return [GitCommitTaskRef.from_entry(entry, repo_id) for entry in res]


async def list_commit_task_refs_by_task(
    repo_id: int,
    task_id: int,
    page: int,
    perpage: int,
) -> Page[GitCommitTaskRef]:
    repo_entry = await _search_repo_by_id(repo_id)
    repo_name = str(repo_entry["cn"][0])
    classes = _task_ref_filter()
    client = get_client()
    async with client.connect(is_async=True) as conn:
        res = await conn.search(
            _repo_dn(repo_name),
            LDAPSearchScope.ONELEVEL,
            f"(&{classes}(gitTaskId={task_id}))",
        )
    data = [GitCommitTaskRef.from_entry(entry, repo_id) for entry in res]
    data.sort(key=lambda r: r.created_at or datetime.min, reverse=True)
    total = len(data)
    pages = ceil(total / perpage) if perpage else 1
    if total > 0 and page > pages:
        raise HTTPException(status_code=404, detail="No such page")
    offset = max(page - 1, 0) * perpage
    page_data = data[offset : offset + perpage]
    return Page(total=total, page=page, pages=pages, perpage=perpage, data=page_data)


async def get_commit_task_ref_map(repo_id: int) -> dict[str, list[dict]]:
    refs = await list_commit_task_refs_by_commit(repo_id, "")
    result: dict[str, list[dict]] = {}
    for ref in refs:
        result.setdefault(ref.commit_sha, []).append({
            "task_id": ref.task_id,
            "relation": ref.relation,
        })
    return result
