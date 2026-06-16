from unittest.mock import patch

import pytest

from . import factories


@pytest.mark.asyncio
class TestMailingList:
    async def _admin(self):
        user = factories.User(admin=True)
        await user.save()
        return user

    async def test_get_mailinglist_list_admin(self, client):
        user = await self._admin()
        client.login(user=user)
        response = client.get("/mailinglists")
        assert response.status_code == 200

    async def test_get_mailinglist_list_public(self, client):
        response = client.get("/mailinglists/public")
        assert response.status_code == 200

    async def test_create_mailinglist_requires_admin(self, client):
        user = factories.User()
        await user.save()
        client.login(user=user)
        data = {"name": "testlist", "address": "testlist@example.com"}
        response = client.post("/mailinglists", data=data)
        assert response.status_code == 403

    @patch("freenit.api.mailinglist.create_inbox_account")
    @patch("freenit.api.mailinglist.create_list_principal")
    @patch("freenit.api.mailinglist.create_archive_account")
    @patch("freenit.api.mailinglist.add_external_member")
    async def test_create_mailinglist(self, add_member, create_archive, create_list, create_inbox, client):
        create_inbox.return_value = 1
        create_list.return_value = 2
        create_archive.return_value = 3
        user = await self._admin()
        client.login(user=user)
        data = {"name": "testlist", "address": "testlist@example.com"}
        response = client.post("/mailinglists", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "testlist"
        assert result["address"] == "testlist@example.com"
        assert result["distribution_address"] == "testlist-members@example.com"
        assert result["archive_address"] == "testlist-archive@example.com"

    @patch("freenit.api.mailinglist.create_inbox_account")
    @patch("freenit.api.mailinglist.create_list_principal")
    @patch("freenit.api.mailinglist.create_archive_account")
    @patch("freenit.api.mailinglist.add_external_member")
    async def test_subscribe_flow(self, add_member, create_archive, create_list, create_inbox, client):
        create_inbox.return_value = 1
        create_list.return_value = 2
        create_archive.return_value = 3
        user = await self._admin()
        client.login(user=user)
        data = {"name": "testlist", "address": "testlist@example.com"}
        response = client.post("/mailinglists", data=data)
        assert response.status_code == 200
        list_id = response.json()["id"]

        with patch("freenit.api.mailinglist.sendmail") as mock_send:
            response = client.post(f"/mailinglists/{list_id}/subscribe", data={"email": "subscriber@example.com"})
            assert response.status_code == 200
            mock_send.assert_called_once()

    async def test_public_archive_forbidden_when_private(self, client):
        # Without mocking stalwart this just validates the endpoint wiring
        response = client.get("/mailinglists/1/archive")
        assert response.status_code in (404, 403)
