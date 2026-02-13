from unittest.mock import patch, MagicMock
from daily_update_helpers.late_night_web_scraper import WaitlistEntry


def make_connection():
    with patch("daily_update_helpers.daily_updates_dynamo_db_connection.boto3") as mock_boto:
        mock_table = MagicMock()
        mock_boto.resource.return_value.Table.return_value = mock_table
        from daily_update_helpers.daily_updates_dynamo_db_connection import DailyUpdateDynamoDbConnection
        conn = DailyUpdateDynamoDbConnection()
        return conn, mock_table


class TestGetShowObjectFromDb:
    def test_found(self):
        conn, mock_table = make_connection()
        mock_table.get_item.return_value = {"Item": {"id": "Show", "Waitlists": []}}
        result = conn.get_show_object_from_db("Show")
        assert result["id"] == "Show"

    def test_not_found_creates_new(self):
        conn, mock_table = make_connection()
        mock_table.get_item.return_value = {}
        result = conn.get_show_object_from_db("New Show")
        assert result == {"id": "New Show"}


class TestUpdateWaitlistForShow:
    def test_puts_item_with_waitlists(self):
        conn, mock_table = make_connection()
        mock_table.get_item.return_value = {"Item": {"id": "Show", "Waitlists": []}}
        entries = [WaitlistEntry("Mon", "Show", "Join", "5pm")]
        conn.update_waitlist_for_show("Show", entries)
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]["Item"]
        assert len(item["Waitlists"]) == 1
        assert item["Waitlists"][0]["Date"] == "Mon"


class TestUpdateVolunteeringForOrg:
    def test_puts_item_with_opportunities(self):
        conn, mock_table = make_connection()
        mock_table.get_item.return_value = {"Item": {"id": "NYC"}}
        opps = [{"title": "Cleanup", "date": "2026-03-14"}]
        conn.update_volunteering_for_org("NYC", opps)
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["Volunteering Opportunities"] == opps


class TestGetShowWaitlistEntriesFromDb:
    def test_returns_entries(self):
        conn, mock_table = make_connection()
        mock_table.get_item.return_value = {
            "Item": {
                "id": "Show",
                "Waitlists": [{"Date": "Mon", "Time": "5pm", "ButtonText": "Join"}],
            }
        }
        result = conn.get_show_waitlist_entries_from_db("Show")
        assert len(result) == 1
        assert result[0].date == "Mon"

    def test_not_found(self):
        conn, mock_table = make_connection()
        mock_table.get_item.return_value = {}
        result = conn.get_show_waitlist_entries_from_db("Missing")
        assert result == []


class TestGetVolunteeringForOrg:
    def test_returns_opps(self):
        conn, mock_table = make_connection()
        mock_table.get_item.return_value = {
            "Item": {"id": "NYC", "Volunteering Opportunities": [{"title": "Cleanup"}]}
        }
        result = conn.get_volunteering_for_org("NYC")
        assert len(result) == 1

    def test_not_found(self):
        conn, mock_table = make_connection()
        mock_table.get_item.return_value = {}
        result = conn.get_volunteering_for_org("Missing")
        assert result == []
