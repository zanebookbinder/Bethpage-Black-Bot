import logging
from datetime import datetime, timedelta
from itertools import groupby

from lambda_helpers.date_handler import EASTERN, now_eastern
from lambda_helpers.email_log import EmailLog
from lambda_helpers.email_sender import EmailSender

logger = logging.getLogger(__name__)

REPORT_WEEKDAY = 6  # datetime.weekday(): Monday == 0, Sunday == 6
REPORT_HOUR_ET = 19  # 7pm Eastern
REPORT_WINDOW_DAYS = 7

MONTH_NUMBERS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}


class WeeklyEmailReport:
    """Builds and sends the weekly "Bethpage Black Bot Email Report" admin email.

    The report always covers the trailing REPORT_WINDOW_DAYS, so it produces a
    correct summary whenever it is run — not just on Sundays.
    """

    def __init__(self, email_log=None, email_sender=None):
        self.email_log = email_log if email_log is not None else EmailLog()
        self._email_sender = email_sender

    @property
    def email_sender(self):
        if self._email_sender is None:
            self._email_sender = EmailSender()
        return self._email_sender

    @staticmethod
    def is_report_time(now_et):
        """True on Sunday from 7pm Eastern onward."""
        return now_et.weekday() == REPORT_WEEKDAY and now_et.hour >= REPORT_HOUR_ET

    @staticmethod
    def week_key(now_et):
        """Identifies the Sunday a report belongs to, so only the first
        qualifying run of the evening actually sends one."""
        return now_et.date().isoformat()

    def send_report_if_due(self):
        """Send the report if this is the first Sunday-evening run after 7pm ET."""
        now_et = now_eastern()
        if not self.is_report_time(now_et):
            return False

        week_key = self.week_key(now_et)
        if self.email_log.has_report_been_sent(week_key):
            logger.debug("Weekly email report already sent for week of %s", week_key)
            return False

        self.send_report(now_et=now_et, week_key=week_key)
        return True

    def build_current_report(self, now_et=None):
        """Returns (body_html, email_count) for the trailing week."""
        now_et = now_et or now_eastern()
        cutoff = now_et - timedelta(days=REPORT_WINDOW_DAYS)
        records = self.email_log.get_emails_sent_since(cutoff)
        return self.build_report_html(records, now_et, cutoff), len(records)

    def send_report(self, now_et=None, week_key=None):
        """Build and send the report for the trailing week. Always sends."""
        now_et = now_et or now_eastern()
        body_html, email_count = self.build_current_report(now_et)

        self.email_sender.send_weekly_email_report(body_html)
        logger.info("Sent weekly email report covering %d emails", email_count)

        if week_key:
            self.email_log.mark_report_sent(week_key, email_count)
        return email_count

    # ---------- formatting ----------

    @staticmethod
    def format_clock_time(time_str, drop_zero_minutes=False):
        """'04:00PM' / '4:00pm' -> '4:00pm', or '4pm' when dropping :00."""
        try:
            parsed = datetime.strptime(time_str.strip(), "%I:%M%p")
        except (ValueError, AttributeError):
            return time_str
        meridiem = "am" if parsed.hour < 12 else "pm"
        hour = parsed.hour % 12 or 12
        if drop_zero_minutes and parsed.minute == 0:
            return f"{hour}{meridiem}"
        return f"{hour}:{parsed.minute:02d}{meridiem}"

    @staticmethod
    def _parse_sent_at(sent_at):
        """Stored stamps are Eastern ISO; fall back to raw text if unparseable."""
        try:
            sent_dt = datetime.fromisoformat(str(sent_at))
        except ValueError:
            return None
        if sent_dt.tzinfo is None:
            sent_dt = sent_dt.replace(tzinfo=EASTERN)
        return sent_dt.astimezone(EASTERN)

    @classmethod
    def format_email_date(cls, sent_at):
        """'2026-08-25T14:44:03-04:00' -> '8/25/2026'."""
        et = cls._parse_sent_at(sent_at)
        if et is None:
            return str(sent_at)
        return f"{et.month}/{et.day}/{et.year}"

    @classmethod
    def format_email_time(cls, sent_at):
        """'2026-08-25T14:44:03-04:00' -> '2:44pm'."""
        et = cls._parse_sent_at(sent_at)
        if et is None:
            return str(sent_at)
        return cls.format_clock_time(et.strftime("%I:%M%p"))

    @classmethod
    def format_tee_time_slot(cls, tee_time):
        """{'Date': 'Wednesday August 30th', 'Time': '4:00pm'}
        -> 'Wednesday 8/30 at 4pm'."""
        date_str = str(tee_time.get("Date", "")).strip()
        time_str = cls.format_clock_time(
            str(tee_time.get("Time", "")), drop_zero_minutes=True
        )

        parts = date_str.split()
        if len(parts) >= 3 and parts[1] in MONTH_NUMBERS:
            day_of_week = parts[0]
            month = MONTH_NUMBERS[parts[1]]
            day_digits = "".join(c for c in parts[2] if c.isdigit())
            if day_digits:
                return f"{day_of_week} {month}/{int(day_digits)} at {time_str}"

        # Unrecognized date format — show it as-is rather than dropping the row.
        return f"{date_str} at {time_str}" if date_str else time_str

    @classmethod
    def group_records(cls, records):
        """Collapse per-user records into one row per (run, tee time slot),
        oldest run first, with the users notified joined together."""
        rows = {}
        for record in records:
            sent_at = record.get("sent_at", "")
            user_email = record.get("user_email", "")
            for tee_time in record.get("tee_times", []) or []:
                slot = cls.format_tee_time_slot(tee_time)
                key = (sent_at, slot)
                rows.setdefault(
                    key,
                    {
                        "sent_at": sent_at,
                        # Sort on the epoch, not the Eastern string: the hour
                        # that repeats when EDT rolls back to EST would
                        # otherwise sort out of order.
                        "sent_at_epoch": int(record.get("sent_at_epoch", 0)),
                        "slot": slot,
                        "users": [],
                    },
                )
                if user_email and user_email not in rows[key]["users"]:
                    rows[key]["users"].append(user_email)

        return sorted(rows.values(), key=lambda r: (r["sent_at_epoch"], r["slot"]))

    @classmethod
    def build_report_html(cls, records, now_et, cutoff_et):
        total_emails = len(records)
        rows = list(cls.group_records(records))

        cell_style = "border: 1px solid #ddd; padding: 8px; vertical-align: top;"
        header_style = f"{cell_style} background-color: #f0f0f0; text-align: left;"

        date_range = (
            f"{cutoff_et.month}/{cutoff_et.day}/{cutoff_et.year} – "
            f"{now_et.month}/{now_et.day}/{now_et.year}"
        )

        html_lines = [
            "<html><body style=\"font-family: 'Roboto', Arial, sans-serif;\">",
            "<h2>Bethpage Black Bot Email Report</h2>",
            f"<p style='font-size: 1.1em;'><strong>Total emails sent: {total_emails}</strong></p>",
            f"<p style='color: #666;'>Covering {date_range} (last {REPORT_WINDOW_DAYS} days).</p>",
        ]

        if not rows:
            html_lines.append("<p>No tee time notification emails were sent this week.</p>")
        else:
            html_lines += [
                "<table style='border-collapse: collapse; width: auto;'>",
                "<thead><tr>"
                f"<th style='{header_style}'>Email Date</th>"
                f"<th style='{header_style}'>Email Time</th>"
                f"<th style='{header_style}'>Tee Time Slot</th>"
                f"<th style='{header_style}'>Users Notified</th>"
                "</tr></thead>",
                "<tbody>",
            ]
            # Rows are already in ascending time order, so same-date rows are
            # contiguous and the date cell can span them.
            for _, day_rows in groupby(rows, key=lambda r: cls.format_email_date(r["sent_at"])):
                day_rows = list(day_rows)
                for i, row in enumerate(day_rows):
                    users = ", ".join(sorted(row["users"], key=str.lower))
                    html_lines.append("<tr>")
                    if i == 0:
                        html_lines.append(
                            f"<td style='{cell_style}' rowspan='{len(day_rows)}'>"
                            f"{cls.format_email_date(row['sent_at'])}</td>"
                        )
                    html_lines.append(
                        f"<td style='{cell_style}'>{cls.format_email_time(row['sent_at'])}</td>"
                        f"<td style='{cell_style}'>{row['slot']}</td>"
                        f"<td style='{cell_style}'>{users}</td>"
                        "</tr>"
                    )
            html_lines.append("</tbody></table>")

        html_lines.append("</body></html>")
        return "".join(html_lines)
