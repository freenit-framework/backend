from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from freenit.models.ldap.base import LDAPBaseModel


class NotFoundError(Exception):
    pass


class IntegrityError(Exception):
    pass


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


def _bool(entry, attr, default=False):
    value = _first(entry, attr)
    if value is None:
        return default
    return str(value).upper() == "TRUE"


def _datetime(entry, attr, default=None):
    value = _first(entry, attr)
    if value is None:
        return default
    value = str(value)
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


class GitRepo(LDAPBaseModel):
    id: int = Field(0, description="Numeric repository ID")
    project_id: int = Field(0, description="Parent project ID")
    name: str = Field("", description="Repository name")
    path: str = Field("", description="Filesystem path to the bare repository")
    description: str | None = Field(None, description="Optional description")
    public: bool = Field(False, description="Publicly visible")
    default_branch: str = Field("main", description="Default branch name")
    tests_enabled: bool = Field(False, description="Run tests on push")
    test_command: str | None = Field(None, description="Shell command used for tests")
    webhook_url: str | None = Field(None, description="URL to notify on push")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    @classmethod
    def from_entry(cls, entry):
        return cls(
            dn=str(entry["dn"]),
            id=_int(entry, "gitIdNumber", 0),
            project_id=_int(entry, "gitProjectId", 0),
            name=_first(entry, "cn", ""),
            path=_first(entry, "gitPath", ""),
            description=_first(entry, "description"),
            public=_bool(entry, "gitPublic", False),
            default_branch=_first(entry, "gitDefaultBranch", "main"),
            tests_enabled=_bool(entry, "gitTestsEnabled", False),
            test_command=_first(entry, "gitTestCommand"),
            webhook_url=_first(entry, "gitWebhookUrl"),
            created_at=_datetime(entry, "createdAt"),
            updated_at=_datetime(entry, "updatedAt"),
        )


class GitPermission(LDAPBaseModel):
    id: int = Field(0, description="Numeric permission ID")
    repo_id: int = Field(0, description="Parent repository ID")
    user_email: str = Field("", description="User email")
    access: str = Field("read", description="read/write/admin")
    created_at: datetime | None = Field(None, description="Creation timestamp")

    @classmethod
    def from_entry(cls, entry, repo_id: int = 0):
        return cls(
            dn=str(entry["dn"]),
            id=_int(entry, "gitIdNumber", 0),
            repo_id=repo_id,
            user_email=_first(entry, "mail", ""),
            access=_first(entry, "gitAccess", "read"),
            created_at=_datetime(entry, "createdAt"),
        )


class GitPushLog(LDAPBaseModel):
    id: int = Field(0, description="Numeric push log ID")
    repo_id: int = Field(0, description="Parent repository ID")
    ref: str = Field("", description="Git ref")
    old_rev: str | None = Field(None, description="Old revision")
    new_rev: str | None = Field(None, description="New revision")
    pusher_email: str = Field("", description="Pusher email")
    status: str = Field("pending", description="pending/completed/success/failure")
    output: str | None = Field(None, description="Test output")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    @classmethod
    def from_entry(cls, entry, repo_id: int = 0):
        return cls(
            dn=str(entry["dn"]),
            id=_int(entry, "gitIdNumber", 0),
            repo_id=repo_id,
            ref=_first(entry, "gitRef", ""),
            old_rev=_first(entry, "gitOldRev"),
            new_rev=_first(entry, "gitNewRev"),
            pusher_email=_first(entry, "gitPusherEmail", ""),
            status=_first(entry, "gitStatus", "pending"),
            output=_first(entry, "gitOutput"),
            created_at=_datetime(entry, "createdAt"),
            updated_at=_datetime(entry, "updatedAt"),
        )


class GitCommitTaskRef(LDAPBaseModel):
    id: int = Field(0, description="Numeric task reference ID")
    repo_id: int = Field(0, description="Parent repository ID")
    task_id: int = Field(0, description="Referenced task ID")
    commit_sha: str = Field("", description="Git commit SHA")
    relation: str = Field("refer", description="fix or refer")
    created_at: datetime | None = Field(None, description="Creation timestamp")

    @classmethod
    def from_entry(cls, entry, repo_id: int = 0):
        return cls(
            dn=str(entry["dn"]),
            id=_int(entry, "gitIdNumber", 0),
            repo_id=repo_id,
            task_id=_int(entry, "gitTaskId", 0),
            commit_sha=_first(entry, "gitCommitSha", ""),
            relation=_first(entry, "gitRelation", "refer"),
            created_at=_datetime(entry, "createdAt"),
        )


class GitRepoCreate(BaseModel):
    name: str
    path: str
    project_id: int
    description: str | None = None
    public: bool = False
    default_branch: str = "main"
    tests_enabled: bool = False
    test_command: str | None = None
    webhook_url: str | None = None


class GitRepoUpdate(BaseModel):
    name: str | None = None
    path: str | None = None
    project_id: int | None = None
    description: str | None = None
    public: bool | None = None
    default_branch: str | None = None
    tests_enabled: bool | None = None
    test_command: str | None = None
    webhook_url: str | None = None
