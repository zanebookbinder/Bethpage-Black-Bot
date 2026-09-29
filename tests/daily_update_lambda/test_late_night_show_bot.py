from unittest.mock import patch, MagicMock
from daily_update_helpers.late_night_web_scraper import WaitlistEntry
from daily_update_helpers.last_week_tonight_web_scraper import (
    LastWeekTonightEntry,
    TicketStatus,
)


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


class TestJohnOliverHtml:
    def test_build_john_oliver_html(self):
        bot = make_bot()
        entries = [
            LastWeekTonightEntry("Sat 17 October, 2026", TicketStatus.AVAILABLE, "Showtime: 5:00PM"),
            LastWeekTonightEntry(
                "Sat 24 October, 2026 - 5:00PM",
                TicketStatus.NOT_YET_RELEASED,
                "Tickets available on Oct 6th @ 3PM",
            ),
        ]
        html = bot.build_john_oliver_html(entries)
        assert "Last Week Tonight with John Oliver" in html
        assert "Sat 17 October, 2026" in html
        assert "Request Tickets" in html
        assert "Sat 24 October, 2026 - 5:00PM" in html
        assert "Not Yet Released" in html
        assert "Tickets available on Oct 6th @ 3PM" in html

    def test_john_oliver_section_appears_before_1iota_table(self):
        bot = make_bot()
        jo_entries = [
            LastWeekTonightEntry("Sat 17 October, 2026", TicketStatus.AVAILABLE, "Showtime: 5:00PM"),
        ]
        iota_entries = {
            "The Daily Show": [
                WaitlistEntry("Mon Jan 5", "The Daily Show", "Join Waitlist", "5:00 PM"),
            ]
        }
        html = bot.build_waitlist_html(iota_entries, jo_entries)
        assert html.index("Last Week Tonight with John Oliver") < html.index("The Daily Show")

    def test_john_oliver_only_still_renders_without_1iota_table(self):
        bot = make_bot()
        jo_entries = [
            LastWeekTonightEntry("Sat 17 October, 2026", TicketStatus.AVAILABLE, "Showtime: 5:00PM"),
        ]
        html = bot.build_waitlist_html({}, jo_entries)
        assert "Last Week Tonight with John Oliver" in html
        assert "Sat 17 October, 2026" in html

    def test_scrape_john_oliver_entries_failure_returns_empty_list(self):
        bot = make_bot()
        with patch("late_night_show_bot.LastWeekTonightWebScraper") as mock_scraper_cls:
            mock_scraper = MagicMock()
            mock_scraper.find_available_and_upcoming_tapings.side_effect = Exception("boom")
            mock_scraper_cls.return_value = mock_scraper

            result = bot.scrape_john_oliver_entries()

        assert result == []
        mock_scraper.close.assert_called_once()


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
