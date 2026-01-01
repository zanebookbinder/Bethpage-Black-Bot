from daily_update_helpers.new_york_cares_web_scraper import NewYorkCaresWebScraper
from daily_update_helpers.daily_updates_dynamo_db_connection import (
    DailyUpdateDynamoDbConnection,
)
import traceback
from daily_update_helpers.daily_updates_email_service import (
    DailyUpdateEmailService,
)
from datetime import datetime

class NewYorkCaresBot:
    def notify_if_new_volunteering_opportunities(self):
        print("Starting New York Cares volunteering opportunity notification process")

        try:
            # Build the email HTML but do not send (daily_updates_email_service will send)
            body_html = self.scrape_data_and_return_email_html()
            return body_html

        except Exception as e:
            print("Exception:", e)
            error_message = traceback.format_exc()
            DailyUpdateEmailService().send_error_email(error_message)
            raise e

    def scrape_data_and_return_email_html(self):
        """Scrape NY Cares, diff with DB, update DB, and return HTML for new opportunities."""
        scraper = NewYorkCaresWebScraper()
        db = DailyUpdateDynamoDbConnection()

        current = scraper.find_weekend_opportunities()
        if not current:
            return None

        # update DB with current (overwrite)
        db.update_volunteering_for_org("New York Cares", current)

        return self.build_volunteer_email(current)

    def build_volunteer_email(self, volunteer_list):
        """Return HTML for volunteer opportunities as a table grouped by date ascending (closest to today first)."""
        if not volunteer_list:
            return ""

        def format_date(date_obj):
            return (
                date_obj.strftime("%B %d")
                + (
                    "th"
                    if 4 <= date_obj.day <= 20
                    else {1: "st", 2: "nd", 3: "rd"}.get(date_obj.day % 10, "th")
                )
                + f", {date_obj.year}"
            )

        # group parsed dates, keep unknowns separate
        grouped = {}
        for opp in volunteer_list:
            raw_date = opp.get("date") or ""
            pd = None
            try:
                pd = datetime.fromisoformat(raw_date).date() if raw_date else None
            except Exception:
                pd = None
            if pd:
                grouped.setdefault(pd, []).append(opp)
            else:
                print("Date unknown for opportunity:", opp)

        sorted_dates = sorted(grouped.keys())

        html_lines = [
            "<div>",
            "<h2>Volunteering Opportunities (New York Cares)</h2>",
            "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>",
            "<thead><tr><th>Date</th><th>Title</th><th>Time</th><th>Location</th><th>Transit Time</th><th>Walking Time</th><th>Link</th></tr></thead>",
            "<tbody>",
        ]

        def safe(val, fallback="(unknown)"):
            return val if val else fallback

        # render parsed-date groups
        for pd in sorted_dates:
            entries = grouped[pd]
            date_label = format_date(pd)
            for i, opp in enumerate(entries):
                title = safe(opp.get("title"), "(no title)")
                time = safe(opp.get("time"), "(time unknown)")
                location = safe(opp.get("location"), "(location unknown)")
                transit_time = safe(opp.get("transit_time"), "")
                walking_time = safe(opp.get("walking_time"), "")
                link = opp.get("link") or ""
                link_html = f'<a href="{link}">Click here</a>' if link else ""
                row = "<tr>"
                if i == 0:
                    row += f"<td rowspan='{len(entries)}'>{date_label}</td>"
                row += f"<td>{title}</td><td style=\"white-space: nowrap;\">{time}</td><td>{location}</td><td>{transit_time}</td><td>{walking_time}</td><td>{link_html}</td></tr>"
                html_lines.append(row)

        html_lines += ["</tbody></table></div>"]

        return "".join(["<html><body>"] + html_lines + ["</body></html>"])
