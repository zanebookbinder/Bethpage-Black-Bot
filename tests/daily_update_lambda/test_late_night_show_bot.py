from unittest.mock import patch, MagicMock
from daily_update_helpers.late_night_web_scraper import WaitlistEntry


def make_bot():
    with patch("late_night_show_bot.DailyUpdateDynamoDbConnection"), \
         patch("late_night_show_bot.DailyUpdateEmailService"):
        from late_night_show_bot import LateNightShowBot
        return LateNightShowBot()


class TestBuildWaitlistHtml:
    def test_basic_html(self):
        bot = make_bot()
        entries = {
            "The Daily Show": [
                WaitlistEntry("Mon Jan 5", "The Daily Show", "Join Waitlist", "5:00 PM"),
            ]
        }
        html = bot.build_waitlist_html(entries)
        assert "The Daily Show" in html
        assert "Mon Jan 5" in html
        assert "5:00 PM" in html
        assert "Join Waitlist" in html
        assert "<table" in html

    def test_multiple_shows(self):
        bot = make_bot()
        entries = {
            "The Daily Show": [
                WaitlistEntry("Mon Jan 5", "The Daily Show", "Join Waitlist", "5:00 PM"),
            ],
            "The Late Show with Stephen Colbert": [
                WaitlistEntry("Tue Jan 6", "The Late Show with Stephen Colbert", "Request Tickets", "6:00 PM"),
            ],
        }
        html = bot.build_waitlist_html(entries)
        assert "The Daily Show" in html
        assert "The Late Show with Stephen Colbert" in html


class TestFilterEntriesForTime:
    def test_filters_early_times(self):
        bot = make_bot()
        entries = {
            "Show": [
                WaitlistEntry("Mon", "Show", "Join", "5:00 PM"),  # starts with 5 > 3, keep
                WaitlistEntry("Mon", "Show", "Join", "2:00 PM"),  # starts with 2 <= 3, remove
                WaitlistEntry("Mon", "Show", "Join", "4:30 PM"),  # starts with 4 > 3, keep
            ]
        }
        result = bot.filter_entries_for_time(entries)
        assert "Show" in result
        assert len(result["Show"]) == 2

    def test_all_filtered_removes_show(self):
        bot = make_bot()
        entries = {
            "Show": [
                WaitlistEntry("Mon", "Show", "Join", "1:00 PM"),
                WaitlistEntry("Mon", "Show", "Join", "2:00 PM"),
            ]
        }
        result = bot.filter_entries_for_time(entries)
        assert "Show" not in result
