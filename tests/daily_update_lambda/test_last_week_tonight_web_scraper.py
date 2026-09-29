from unittest.mock import patch, MagicMock

import requests

from daily_update_helpers.last_week_tonight_web_scraper import (
    LastWeekTonightWebScraper,
    TicketStatus,
)

SCHEDULE_HTML = """
<html><body>
<ul id="main_sched">
<li class="sched_line no_more_tix"><span class="sl_day">Sat</span> <span class="sl_date">03</span> <span class="sl_my">October, 2026</span><span class="sl_showtime">Showtime: 5:00PM</span></li>
<li class="sched_line"><span class="sl_day">Sat</span> <span class="sl_date">17</span> <span class="sl_my">October, 2026</span><span class="sl_showtime">Showtime: 5:00PM</span></li>
<li class="sched_line sl_notyet"><span class="sl_day">Sat</span> <span class="sl_date">24</span> <span class="sl_my">October, 2026 - 5:00PM</span><span class="sl_showtime">Tickets available on Oct 6th @ 3PM</span></li>
</ul>
</body></html>
"""


def make_response(text, status=200):
    response = MagicMock()
    response.text = text
    response.status_code = status
    response.raise_for_status = MagicMock()
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(f"{status} error")
    return response


class TestParseSchedule:
    def test_excludes_sold_out_includes_available_and_not_yet_released(self):
        scraper = LastWeekTonightWebScraper()
        with patch.object(
            scraper.session, "get", return_value=make_response(SCHEDULE_HTML)
        ):
            entries = scraper.find_available_and_upcoming_tapings()

        assert len(entries) == 2

        available = next(e for e in entries if e.status == TicketStatus.AVAILABLE)
        assert available.date_text == "Sat 17 October, 2026"
        assert available.detail == "Showtime: 5:00PM"

        not_yet = next(e for e in entries if e.status == TicketStatus.NOT_YET_RELEASED)
        assert not_yet.date_text == "Sat 24 October, 2026 - 5:00PM"
        assert not_yet.detail == "Tickets available on Oct 6th @ 3PM"

    def test_missing_schedule_list_returns_empty(self):
        scraper = LastWeekTonightWebScraper()
        with patch.object(
            scraper.session, "get", return_value=make_response("<html><body>no schedule here</body></html>")
        ):
            entries = scraper.find_available_and_upcoming_tapings()
        assert entries == []

    def test_malformed_line_is_skipped_not_fatal(self):
        html = """
        <ul id="main_sched">
        <li class="sched_line"><span class="sl_day">Sat</span></li>
        <li class="sched_line"><span class="sl_day">Sat</span> <span class="sl_date">17</span> <span class="sl_my">October, 2026</span><span class="sl_showtime">Showtime: 5:00PM</span></li>
        </ul>
        """
        scraper = LastWeekTonightWebScraper()
        with patch.object(scraper.session, "get", return_value=make_response(html)):
            entries = scraper.find_available_and_upcoming_tapings()
        assert len(entries) == 1
        assert entries[0].date_text == "Sat 17 October, 2026"


class TestFetchWithRetries:
    def test_retries_then_succeeds(self):
        scraper = LastWeekTonightWebScraper()
        with patch.object(
            scraper.session,
            "get",
            side_effect=[requests.Timeout("timed out"), make_response(SCHEDULE_HTML)],
        ), patch("daily_update_helpers.last_week_tonight_web_scraper.time.sleep"):
            entries = scraper.find_available_and_upcoming_tapings()
        assert len(entries) == 2

    def test_all_attempts_fail_returns_empty_list(self):
        scraper = LastWeekTonightWebScraper()
        with patch.object(
            scraper.session, "get", side_effect=requests.ConnectionError("down")
        ), patch("daily_update_helpers.last_week_tonight_web_scraper.time.sleep"):
            entries = scraper.find_available_and_upcoming_tapings()
        assert entries == []

    def test_http_error_status_returns_empty_list(self):
        scraper = LastWeekTonightWebScraper()
        with patch.object(
            scraper.session, "get", return_value=make_response("", status=500)
        ), patch("daily_update_helpers.last_week_tonight_web_scraper.time.sleep"):
            entries = scraper.find_available_and_upcoming_tapings()
        assert entries == []
