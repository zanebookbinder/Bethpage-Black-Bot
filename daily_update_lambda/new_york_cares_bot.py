import html
from datetime import datetime

from daily_update_helpers.daily_updates_dynamo_db_connection import (
    DailyUpdateDynamoDbConnection,
)
import traceback
from daily_update_helpers.daily_updates_email_service import (
    DailyUpdateEmailService,
)
from daily_update_helpers.new_york_cares_web_scraper import NewYorkCaresWebScraper


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
            return ""

        # update DB with current (overwrite)
        db.update_volunteering_for_org("New York Cares", current)

        return self.build_volunteer_email(current)

    def build_volunteer_email(self, volunteer_list):
        """Return HTML for volunteer opportunities as a table grouped by date ascending."""
        if not volunteer_list:
            return ""

        def format_date(date_obj):
            suffix = (
                "th"
                if 4 <= date_obj.day <= 20
                else {1: "st", 2: "nd", 3: "rd"}.get(date_obj.day % 10, "th")
            )
            return f"{date_obj.strftime('%B %d')}{suffix}, {date_obj.year}"

        grouped = {}
        for opp in volunteer_list:
            raw_date = opp.get("date") or ""
            try:
                pd = datetime.fromisoformat(raw_date).date() if raw_date else None
            except Exception:
                pd = None
            if pd:
                grouped.setdefault(pd, []).append(opp)
            else:
                print("Date unknown for opportunity:", opp)

        cell_style = "border: 1px solid #ddd; padding: 8px;"
        table_rows = ""
        for pd in sorted(grouped.keys()):
            entries = grouped[pd]
            date_label = html.escape(format_date(pd))
            for i, opp in enumerate(entries):
                title = html.escape(opp.get("title") or "(no title)")
                time_val = html.escape(opp.get("time") or "(time unknown)")
                location = html.escape(opp.get("location") or "(location unknown)")
                transit_time = html.escape(opp.get("transit_time") or "")
                walking_time = html.escape(opp.get("walking_time") or "")
                link = opp.get("link") or ""
                link_html = (
                    f'<a href="{html.escape(link)}" target="_blank">Sign Up</a>'
                    if link
                    else ""
                )
                row = "<tr>"
                if i == 0:
                    row += f'<td style="{cell_style}" rowspan="{len(entries)}">{date_label}</td>'
                row += f'<td style="{cell_style}">{title}</td>'
                row += f'<td style="{cell_style} white-space: nowrap;">{time_val}</td>'
                row += f'<td style="{cell_style}">{location}</td>'
                row += f'<td style="{cell_style}">{transit_time}</td>'
                row += f'<td style="{cell_style}">{walking_time}</td>'
                row += f'<td style="{cell_style}">{link_html}</td></tr>'
                table_rows += row

        return f"""
        <h2>Volunteering Opportunities (New York Cares)</h2>
        <table style="width:100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="{cell_style} text-align: left;">Date</th>
                    <th style="{cell_style} text-align: left;">Title</th>
                    <th style="{cell_style} text-align: left;">Time</th>
                    <th style="{cell_style} text-align: left;">Location</th>
                    <th style="{cell_style} text-align: left;">Transit Time</th>
                    <th style="{cell_style} text-align: left;">Walking Time</th>
                    <th style="{cell_style} text-align: left;">Link</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        """
