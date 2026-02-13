from unittest.mock import patch, MagicMock


def make_scraper():
    with patch("daily_update_helpers.new_york_cares_web_scraper.create_headless_chrome_driver") as mock_chrome, \
         patch("daily_update_helpers.new_york_cares_web_scraper.TravelTimeCalculationService"):
        mock_chrome.return_value = (MagicMock(), MagicMock())
        from daily_update_helpers.new_york_cares_web_scraper import NewYorkCaresWebScraper
        return NewYorkCaresWebScraper()


class TestFormatTime:
    def test_morning(self):
        s = make_scraper()
        assert s.format_time("08:30") == "8:30AM"

    def test_afternoon(self):
        s = make_scraper()
        assert s.format_time("13:45") == "1:45PM"

    def test_noon(self):
        s = make_scraper()
        assert s.format_time("12:00") == "12:00PM"

    def test_midnight(self):
        s = make_scraper()
        assert s.format_time("00:00") == "12:00AM"

    def test_invalid_input(self):
        s = make_scraper()
        assert s.format_time("not-a-time") == "not-a-time"

    def test_single_part(self):
        s = make_scraper()
        assert s.format_time("0830") == "0830"
