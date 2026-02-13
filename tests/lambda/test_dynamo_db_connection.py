from unittest.mock import patch, MagicMock, call


def make_connection():
    with patch("lambda_helpers.dynamo_db_connection.boto3") as mock_boto:
        mock_dynamodb = MagicMock()
        mock_boto.resource.return_value = mock_dynamodb
        mock_table = MagicMock()
        mock_config_table = MagicMock()
        mock_dynamodb.Table.side_effect = lambda name: {
            "tee-times": mock_table,
            "bethpage-black-bot-config": mock_config_table,
        }[name]

        from lambda_helpers.dynamo_db_connection import DynamoDBConnection
        conn = DynamoDBConnection()
        return conn, mock_table, mock_config_table


class TestPublishTeeTimes:
    def test_puts_both_items(self):
        conn, mock_table, _ = make_connection()
        conn.publish_teetimes(["time1"], {"user": ["time1"]})
        assert mock_table.put_item.call_count == 2

    def test_latest_item_has_correct_id(self):
        conn, mock_table, _ = make_connection()
        conn.publish_teetimes([], {})
        calls = mock_table.put_item.call_args_list
        latest_call = [c for c in calls if c[1]["Item"]["id"] == "latest-tee-times"]
        assert len(latest_call) == 1


class TestGetLatestTeeTimesObject:
    def test_found(self):
        conn, mock_table, _ = make_connection()
        mock_table.get_item.return_value = {"Item": {"id": "latest-tee-times", "all_tee_times": []}}
        result = conn.get_latest_tee_times_object()
        assert result["id"] == "latest-tee-times"

    def test_not_found(self):
        conn, mock_table, _ = make_connection()
        mock_table.get_item.return_value = {}
        result = conn.get_latest_tee_times_object()
        assert result is None


class TestGetAllEmailsList:
    def test_returns_emails(self):
        conn, _, mock_config = make_connection()
        mock_config.get_item.return_value = {
            "Item": {"id": "all-emails", "emails": ["a@b.com", "c@d.com"]}
        }
        result = conn.get_all_emails_list()
        assert result == ["a@b.com", "c@d.com"]

    def test_not_found(self):
        conn, _, mock_config = make_connection()
        mock_config.get_item.return_value = {}
        result = conn.get_all_emails_list()
        assert result is None


class TestAddEmailToAllEmailsList:
    def test_add_new_email(self):
        conn, _, mock_config = make_connection()
        mock_config.get_item.return_value = {
            "Item": {"id": "all-emails", "emails": ["a@b.com"]}
        }
        success, msg = conn.add_email_to_all_emails_list("new@test.com")
        assert success is True
        mock_config.put_item.assert_called_once()

    def test_duplicate_email(self):
        conn, _, mock_config = make_connection()
        mock_config.get_item.return_value = {
            "Item": {"id": "all-emails", "emails": ["a@b.com"]}
        }
        success, msg = conn.add_email_to_all_emails_list("a@b.com")
        assert success is False
        assert "already" in msg.lower()


class TestGetUserConfig:
    def test_found(self):
        conn, _, mock_config = make_connection()
        mock_config.get_item.return_value = {"Item": {"id": "a@b.com", "min_players": 2}}
        result = conn.get_user_config("a@b.com")
        assert result["min_players"] == 2

    def test_not_found(self):
        conn, _, mock_config = make_connection()
        mock_config.get_item.return_value = {}
        result = conn.get_user_config("a@b.com")
        assert result is None


class TestCreateOrUpdateUserConfig:
    def test_puts_config_item(self):
        conn, _, mock_config = make_connection()
        conn.create_or_update_user_config("a@b.com", {"min_players": 3})
        mock_config.put_item.assert_called_once()
        item = mock_config.put_item.call_args[1]["Item"]
        assert item["id"] == "a@b.com"
        assert item["min_players"] == 3

    def test_defaults_when_no_config(self):
        conn, _, mock_config = make_connection()
        conn.create_or_update_user_config("a@b.com")
        item = mock_config.put_item.call_args[1]["Item"]
        assert item["min_players"] == 2  # default
