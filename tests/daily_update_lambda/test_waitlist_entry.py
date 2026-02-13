from daily_update_helpers.late_night_web_scraper import WaitlistEntry


class TestWaitlistEntry:
    def test_str(self):
        entry = WaitlistEntry("Mon Jan 5", "The Daily Show", "Join Waitlist", "5:00 PM")
        result = str(entry)
        assert "The Daily Show" in result
        assert "Mon Jan 5" in result

    def test_to_dynamo_db_item(self):
        entry = WaitlistEntry("Mon Jan 5", "The Daily Show", "Join Waitlist", "5:00 PM")
        item = entry.to_dynamo_db_item()
        assert item["Date"] == "Mon Jan 5"
        assert item["Time"] == "5:00 PM"
        assert item["ButtonText"] == "Join Waitlist"

    def test_from_dynamo_db_item(self):
        db_item = {"Date": "Mon Jan 5", "Time": "5:00 PM", "ButtonText": "Join Waitlist"}
        entry = WaitlistEntry.from_dynamo_db_item("The Daily Show", db_item)
        assert entry.show_name == "The Daily Show"
        assert entry.date == "Mon Jan 5"
        assert entry.show_time == "5:00 PM"
        assert entry.button_text == "Join Waitlist"

    def test_roundtrip(self):
        original = WaitlistEntry("Tue Feb 10", "Late Night", "Request Tickets", "11:30 PM")
        db_item = original.to_dynamo_db_item()
        restored = WaitlistEntry.from_dynamo_db_item("Late Night", db_item)
        assert restored.date == original.date
        assert restored.show_time == original.show_time
        assert restored.button_text == original.button_text
