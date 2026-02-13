from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from freezegun import freeze_time


def make_handler():
    with patch("lambda_helpers.one_time_link_handler.boto3") as mock_boto:
        mock_table = MagicMock()
        mock_boto.resource.return_value.Table.return_value = mock_table
        from lambda_helpers.one_time_link_handler import OneTimeLinkHandler
        h = OneTimeLinkHandler(expire_minutes=60)
        return h, mock_table


class TestGenerateOneTimeLink:
    def test_returns_correct_keys(self):
        h, _ = make_handler()
        link = h.generate_one_time_link("test@example.com")
        assert "id" in link
        assert link["email"] == "test@example.com"
        assert "expire_time" in link

    def test_uuid_format(self):
        h, _ = make_handler()
        link = h.generate_one_time_link("test@example.com")
        # UUID4 has 36 characters with hyphens
        assert len(link["id"]) == 36

    def test_expire_time_is_future(self):
        h, _ = make_handler()
        link = h.generate_one_time_link("test@example.com")
        expire = datetime.fromisoformat(link["expire_time"])
        assert expire > datetime.now(timezone.utc)


class TestIsOneTimeLinkValid:
    def test_valid_link(self):
        h, _ = make_handler()
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        item = {"expire_time": future, "email": "test@example.com"}
        valid, email = h.is_one_time_link_valid(item)
        assert valid is True
        assert email == "test@example.com"

    def test_expired_link(self):
        h, _ = make_handler()
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        item = {"expire_time": past, "email": "test@example.com"}
        valid, msg = h.is_one_time_link_valid(item)
        assert valid is False
        assert "expired" in msg.lower()

    def test_missing_expire_time(self):
        h, _ = make_handler()
        item = {"email": "test@example.com"}
        valid, msg = h.is_one_time_link_valid(item)
        assert valid is False


class TestValidateOneTimeLinkAndGetEmail:
    def test_item_exists_and_valid(self):
        h, mock_table = make_handler()
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        mock_table.get_item.return_value = {
            "Item": {"id": "guid-1", "email": "a@b.com", "expire_time": future}
        }
        valid, email = h.validate_one_time_link_and_get_email("guid-1")
        assert valid is True
        assert email == "a@b.com"

    def test_item_not_found(self):
        h, mock_table = make_handler()
        mock_table.get_item.return_value = {}
        valid, msg = h.validate_one_time_link_and_get_email("bad-guid")
        assert valid is False
        assert "doesn't exist" in msg.lower()

    def test_exception(self):
        h, mock_table = make_handler()
        mock_table.get_item.side_effect = Exception("DynamoDB error")
        valid, msg = h.validate_one_time_link_and_get_email("guid")
        assert valid is False
        assert "error" in msg.lower()


class TestOneTimeLinkToStr:
    def test_format(self):
        h, _ = make_handler()
        item = {"id": "abc-123", "email": "test@example.com", "expire_time": "2026-01-01T00:00:00"}
        result = h.one_time_link_to_str(item)
        assert "abc-123" in result
        assert "test@example.com" in result


class TestRemoveOldOneTimeLinks:
    def test_removes_expired_keeps_valid(self):
        h, mock_table = make_handler()
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        mock_table.scan.return_value = {
            "Items": [
                {"id": "valid", "email": "a@b.com", "expire_time": future},
                {"id": "expired", "email": "c@d.com", "expire_time": past},
            ]
        }

        h.remove_old_one_time_links()

        # Should delete only the expired one
        mock_table.delete_item.assert_called_once_with(Key={"id": "expired"})
