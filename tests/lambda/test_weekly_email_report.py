import re
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from lambda_helpers.date_handler import EASTERN
from lambda_helpers.weekly_email_report import WeeklyEmailReport


def record(sent_at_iso, user_email, tee_times):
    sent_dt = datetime.fromisoformat(sent_at_iso)
    return {
        "sent_at": sent_at_iso,
        "sent_at_epoch": int(sent_dt.timestamp()),
        "user_email": user_email,
        "tee_times": tee_times,
    }


SLOT_A = [{"Date": "Wednesday August 26th", "Time": "4:00pm", "Players": "4", "Holes": "18"}]
SLOT_B = [{"Date": "Saturday August 29th", "Time": "10:20am", "Players": "2", "Holes": "18"}]


def parse_rows(html):
    """[(rowspan_or_None, [cell text, ...]), ...] for each <tr> in the body."""
    body = html.split("<tbody>")[1].split("</tbody>")[0]
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", body):
        cells = re.findall(r"<td style='[^']*'(?: rowspan='(\d+)')?>(.*?)</td>", tr)
        rows.append((cells[0][0] or None, [c[1] for c in cells]))
    return rows


class TestFormatting:
    def test_email_date(self):
        assert WeeklyEmailReport.format_email_date("2026-08-25T14:44:03-04:00") == "8/25/2026"

    def test_email_time_is_time_only(self):
        assert WeeklyEmailReport.format_email_time("2026-08-25T14:44:03-04:00") == "2:44pm"

    def test_tee_time_slot(self):
        assert WeeklyEmailReport.format_tee_time_slot(SLOT_A[0]) == "Wednesday 8/26 at 4pm"

    def test_tee_time_slot_keeps_non_zero_minutes(self):
        assert WeeklyEmailReport.format_tee_time_slot(SLOT_B[0]) == "Saturday 8/29 at 10:20am"

    def test_unparseable_stamp_falls_back_to_raw(self):
        assert WeeklyEmailReport.format_email_date("not a date") == "not a date"


class TestGroupRecords:
    def test_orders_earliest_first(self):
        records = [
            record("2026-08-20T09:00:00-04:00", "b@x.com", SLOT_B),
            record("2026-08-18T09:00:00-04:00", "a@x.com", SLOT_A),
        ]
        rows = WeeklyEmailReport.group_records(records)
        assert [r["sent_at"] for r in rows] == [
            "2026-08-18T09:00:00-04:00",
            "2026-08-20T09:00:00-04:00",
        ]

    def test_collapses_users_notified_in_same_run(self):
        stamp = "2026-08-18T09:00:00-04:00"
        rows = WeeklyEmailReport.group_records(
            [record(stamp, "b@x.com", SLOT_A), record(stamp, "a@x.com", SLOT_A)]
        )
        assert len(rows) == 1
        assert sorted(rows[0]["users"]) == ["a@x.com", "b@x.com"]

    def test_same_run_different_slots_are_separate_rows(self):
        stamp = "2026-08-18T09:00:00-04:00"
        rows = WeeklyEmailReport.group_records([record(stamp, "a@x.com", SLOT_A + SLOT_B)])
        assert len(rows) == 2


class TestBuildReportHtml:
    def setup_method(self):
        self.now = datetime(2026, 8, 21, 19, 0, tzinfo=EASTERN)
        self.cutoff = self.now - timedelta(days=7)

    def build(self, records):
        return WeeklyEmailReport.build_report_html(records, self.now, self.cutoff)

    def test_total_count_is_number_of_emails_not_rows(self):
        stamp = "2026-08-18T09:00:00-04:00"
        html = self.build([record(stamp, "a@x.com", SLOT_A), record(stamp, "b@x.com", SLOT_A)])
        assert "Total emails sent: 2</strong>" in html
        assert len(parse_rows(html)) == 1

    def test_column_headers(self):
        headers = re.findall(r"<th style='[^']*'>(.*?)</th>", self.build([]))
        assert headers == [] or headers == [
            "Email Date", "Email Time", "Tee Time Slot", "Users Notified",
        ]

    def test_headers_present_when_rows_exist(self):
        html = self.build([record("2026-08-18T09:00:00-04:00", "a@x.com", SLOT_A)])
        assert re.findall(r"<th style='[^']*'>(.*?)</th>", html) == [
            "Email Date", "Email Time", "Tee Time Slot", "Users Notified",
        ]

    def test_date_cell_spans_all_rows_from_that_day(self):
        html = self.build([
            record("2026-08-18T09:00:00-04:00", "a@x.com", SLOT_A),
            record("2026-08-18T15:30:00-04:00", "a@x.com", SLOT_B),
            record("2026-08-19T11:00:00-04:00", "a@x.com", SLOT_A),
        ])
        rows = parse_rows(html)

        # Day one: date cell carries rowspan=2, second row omits the cell entirely.
        # Email Time always keeps minutes; only the tee time slot drops ":00".
        assert rows[0][0] == "2"
        assert rows[0][1] == ["8/18/2026", "9:00am", "Wednesday 8/26 at 4pm", "a@x.com"]
        assert rows[1][0] is None
        assert rows[1][1] == ["3:30pm", "Saturday 8/29 at 10:20am", "a@x.com"]

        # Day two starts a fresh span.
        assert rows[2][0] == "1"
        assert rows[2][1][0] == "8/19/2026"

    def test_empty_report_has_no_table(self):
        html = self.build([])
        assert "Total emails sent: 0</strong>" in html
        assert "<table" not in html
        assert "No tee time notification emails were sent this week." in html


class TestScheduling:
    def test_sunday_after_7pm_is_report_time(self):
        assert WeeklyEmailReport.is_report_time(datetime(2026, 8, 23, 19, 0, tzinfo=EASTERN))

    def test_sunday_before_7pm_is_not(self):
        assert not WeeklyEmailReport.is_report_time(datetime(2026, 8, 23, 18, 59, tzinfo=EASTERN))

    def test_other_weekday_evening_is_not(self):
        assert not WeeklyEmailReport.is_report_time(datetime(2026, 8, 24, 20, 0, tzinfo=EASTERN))

    def test_send_report_if_due_skips_when_marker_exists(self):
        log = MagicMock()
        log.has_report_been_sent.return_value = True
        report = WeeklyEmailReport(email_log=log, email_sender=MagicMock())

        # Not a Sunday evening in real time either, so this must be False regardless.
        assert report.send_report_if_due() is False
        report.email_sender.send_weekly_email_report.assert_not_called()

    def test_send_report_marks_week_when_given_a_key(self):
        log = MagicMock()
        log.get_emails_sent_since.return_value = [
            record("2026-08-18T09:00:00-04:00", "a@x.com", SLOT_A)
        ]
        report = WeeklyEmailReport(email_log=log, email_sender=MagicMock())

        assert report.send_report(week_key="2026-08-23") == 1
        report.email_sender.send_weekly_email_report.assert_called_once()
        log.mark_report_sent.assert_called_once_with("2026-08-23", 1)

    def test_manual_send_without_week_key_does_not_mark(self):
        log = MagicMock()
        log.get_emails_sent_since.return_value = []
        report = WeeklyEmailReport(email_log=log, email_sender=MagicMock())

        report.send_report()
        log.mark_report_sent.assert_not_called()
