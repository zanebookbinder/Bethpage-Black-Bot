from unittest.mock import patch, MagicMock


def make_bot():
    with patch("new_york_cares_bot.DailyUpdateDynamoDbConnection"), \
         patch("new_york_cares_bot.DailyUpdateEmailService"):
        from new_york_cares_bot import NewYorkCaresBot
        return NewYorkCaresBot()


class TestBuildVolunteerEmail:
    def test_basic_html(self):
        bot = make_bot()
        opps = [
            {
                "title": "Park Cleanup",
                "date": "2026-03-14",
                "time": "9:00AM - 12:00PM",
                "location": "Central Park",
                "link": "https://example.com",
                "transit_time": "20 mins",
                "walking_time": "45 mins",
            }
        ]
        html = bot.build_volunteer_email(opps)
        assert "Park Cleanup" in html
        assert "Central Park" in html
        assert "March 14" in html

    def test_empty_list(self):
        bot = make_bot()
        html = bot.build_volunteer_email([])
        assert html == ""

    def test_sorted_by_date(self):
        bot = make_bot()
        opps = [
            {"title": "Later", "date": "2026-03-21", "time": "9AM", "location": "A", "link": "", "transit_time": "", "walking_time": ""},
            {"title": "Earlier", "date": "2026-03-14", "time": "9AM", "location": "B", "link": "", "transit_time": "", "walking_time": ""},
        ]
        html = bot.build_volunteer_email(opps)
        # Earlier date should appear before later date
        assert html.index("March 14") < html.index("March 21")

    def test_invalid_date_skipped(self):
        bot = make_bot()
        opps = [
            {"title": "Bad Date", "date": "not-a-date", "time": "9AM", "location": "A", "link": "", "transit_time": "", "walking_time": ""},
        ]
        html = bot.build_volunteer_email(opps)
        # Should not crash; bad dates are just skipped
        assert "Bad Date" not in html
