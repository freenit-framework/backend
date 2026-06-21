import pytest

from freenit.modules import get_api_modules, get_models, resolve_modules


@pytest.mark.asyncio
class TestModules:
    async def test_resolve_auth_includes_user_and_role(self):
        resolved = resolve_modules(["auth"])
        assert resolved == {"auth", "user", "role"}

    async def test_resolve_project_includes_user_role(self):
        resolved = resolve_modules(["project"])
        assert resolved == {"project", "user", "role"}

    async def test_resolve_multiple_modules(self):
        resolved = resolve_modules(["auth", "project", "mailinglist"])
        assert resolved == {"auth", "project", "mailinglist", "user", "role"}

    async def test_resolve_unknown_module_raises(self):
        with pytest.raises(ValueError):
            resolve_modules(["auth", "unknown"])

    async def test_get_api_modules(self):
        api_modules = get_api_modules(["auth", "project"])
        assert "freenit.api.auth" in api_modules
        assert "freenit.api.project" in api_modules
        assert "freenit.api.mailinglist" not in api_modules

    async def test_get_models(self):
        models = get_models(["auth", "project"])
        assert "freenit.models.sql.base" in models
        assert "freenit.models.sql.project" in models
        assert "freenit.models.sql.mailinglist" not in models

    async def test_discovery_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert "meta" in data
        assert "auth" in data["modules"]
        assert "user" in data["modules"]
        assert "role" in data["modules"]
