from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class Module:
    name: str
    dependencies: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    api: str = ""

    def __hash__(self):
        return hash(self.name)


MODULES = {
    "auth": Module(
        name="auth",
        dependencies=["user", "role"],
        models=["freenit.models.sql.base"],
        api="freenit.api.auth",
    ),
    "user": Module(
        name="user",
        dependencies=["role"],
        api="freenit.api.user",
    ),
    "role": Module(
        name="role",
        dependencies=["user"],
        api="freenit.api.role",
    ),
    "project": Module(
        name="project",
        dependencies=["user"],
        models=["freenit.models.sql.project"],
        api="freenit.api.project",
    ),
    "lms": Module(
        name="lms",
        dependencies=["user"],
        models=["freenit.models.sql.lms"],
        api="freenit.api.lms",
    ),
    "mailinglist": Module(
        name="mailinglist",
        dependencies=["user"],
        models=["freenit.models.sql.mailinglist"],
        api="freenit.api.mailinglist",
    ),
    "domain": Module(
        name="domain",
        dependencies=["user"],
        api="freenit.api.domain",
    ),
    "dav": Module(
        name="dav",
        dependencies=["user"],
        api="freenit.api.dav",
    ),
    "mail": Module(
        name="mail",
        dependencies=["user"],
        api="freenit.api.mail",
    ),
    "sieve": Module(
        name="sieve",
        dependencies=["user"],
        api="freenit.api.sieve",
    ),
    "chat": Module(
        name="chat",
        dependencies=["user"],
        api="freenit.api.chat",
    ),
    "omemo": Module(
        name="omemo",
        dependencies=["user"],
        api="freenit.api.omemo",
    ),
    "git": Module(
        name="git",
        dependencies=["user"],
        models=["freenit.models.sql.git"],
        api="freenit.api.git",
    ),
    "blog": Module(
        name="blog",
        dependencies=["user"],
        models=["freenit.models.sql.blog"],
        api="freenit.api.blog",
    ),
}


def resolve_modules(requested: List[str]) -> Set[str]:
    """Resolve active modules including dependencies.

    Handles circular dependencies by including every module that is part of the
    cycle once any member of the cycle is requested.
    """
    resolved: Set[str] = set()
    stack: List[str] = []

    def visit(name: str) -> None:
        if name in resolved:
            return
        if name in stack:
            # Circular dependency: include every module on the cycle.
            cycle_start = stack.index(name)
            for item in stack[cycle_start:]:
                resolved.add(item)
            return
        module = MODULES.get(name)
        if module is None:
            raise ValueError(f"Unknown freenit module: {name}")
        stack.append(name)
        for dependency in module.dependencies:
            visit(dependency)
        stack.pop()
        resolved.add(name)

    for name in requested:
        visit(name)

    return resolved


def get_api_modules(requested: List[str]) -> List[str]:
    """Return API module import paths for the resolved modules."""
    resolved = resolve_modules(requested)
    return sorted(MODULES[name].api for name in resolved if MODULES[name].api)


def get_models(requested: List[str]) -> List[str]:
    """Return SQL model module paths for migrations."""
    resolved = resolve_modules(requested)
    seen = set()
    models = []
    for name in sorted(resolved):
        for model in MODULES[name].models:
            if model not in seen:
                seen.add(model)
                models.append(model)
    return models
