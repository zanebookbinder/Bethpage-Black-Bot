"""
Central Park private volunteering bot - scrapes MyImpactPage/Better Impact
for volunteer opportunities with space available (login required).
"""

import html
from collections import defaultdict
from datetime import datetime
import holidays
from daily_update_helpers.daily_updates_secret_handler import DailyUpdateSecretHandler
from daily_update_helpers.daily_update_constants import MYIMPACTPAGE_OPPORTUNITIES_URL
from daily_update_helpers.myimpactpage_web_scraper import MyImpactPageWebScraper


class CentralParkPrivateVolunteeringBot:
    """Scrapes Central Park private volunteering opportunities from MyImpactPage."""

    # Date format strings for parsing dates in various formats
    DATE_FORMATS = (
        "%A, %B %d, %Y",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d",
        "%B %d, %Y",
    )

    def __init__(self):
        us_holidays = holidays.UnitedStates(years=datetime.now().year)
        self.holiday_dates = [
            date.strftime("%m/%d/%Y")
            for date, name in us_holidays.items()
            if "Veterans Day" not in name
        ]

    def scrape_data_and_return_email_html(self):
        print(
            "Starting Central Park private volunteering (MyImpactPage) notification process"
        )
        scraper = None
        try:
            username, password = DailyUpdateSecretHandler.get_myimpactpage_credentials()
            if not username or not password:
                print(
                    "MyImpactPage credentials not found in secrets. "
                    "Add myimpactpage-username and myimpactpage-password to daily-updates-secret."
                )
                return self._generate_error_html()

            scraper = MyImpactPageWebScraper()
            if not scraper.login(username, password):
                print("Failed to log in to MyImpactPage")
                return self._generate_error_html()

            opportunities = scraper.get_opportunities_with_space_available()

            return self._generate_email_html(opportunities)

        except Exception as e:
            print(f"Error scraping Central Park private volunteering: {e}")
            return self._generate_error_html()
        finally:
            if scraper:
                scraper.close()

    def _generate_email_html(self, opportunities: list) -> str:
        if not opportunities:
            return (
                "<h2>Central Park Private Volunteering (MyImpactPage)</h2>"
                "<p>No opportunities with space available at this time.</p>"
            )

        # Filter to weekends or holidays
        filtered_opportunities = []
        for opp in opportunities:
            date_str = opp.get("date", "")
            try:
                # Parse date using the same formats as _parse_sort_key
                parsed_date = None
                for fmt in self.DATE_FORMATS:
                    try:
                        parsed_date = datetime.strptime(date_str.strip(), fmt)
                        break
                    except ValueError:
                        continue
                if parsed_date:
                    # Check if weekend (5=Sat, 6=Sun) or holiday
                    is_weekend = parsed_date.weekday() >= 5
                    is_holiday = parsed_date.strftime("%m/%d/%Y") in self.holiday_dates
                    if is_weekend or is_holiday:
                        filtered_opportunities.append(opp)
            except Exception:
                # If parsing fails, skip
                continue

        opportunities = filtered_opportunities

        if not opportunities:
            return (
                "<h2>Central Park Private Volunteering (MyImpactPage)</h2>"
                "<p>No weekend or holiday opportunities with space available at this time.</p>"
            )

        print(
            f"Found {len(opportunities)} shift(s) with space available (filtered to weekends/holidays)"
        )

        # Group by date (date on left, grouped), sort soonest to farthest
        by_date = defaultdict(list)
        for opp in opportunities:
            by_date[opp.get("date", "")].append(opp)

        def _parse_sort_key(date_str: str):
            """Parse date for sorting. Returns (datetime, original) - unparseable go last."""
            for fmt in CentralParkPrivateVolunteeringBot.DATE_FORMATS:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
            return (datetime.max, date_str)

        table_rows = ""
        for date in sorted(by_date.keys(), key=_parse_sort_key):
            shifts = by_date[date]
            date_escaped = html.escape(date)
            for i, opp in enumerate(shifts):
                name = html.escape(opp.get("name", "Opportunity"))
                start_time = html.escape(opp.get("start_time", ""))
                end_time = html.escape(opp.get("end_time", ""))
                open_slots = html.escape(opp.get("open_slots", ""))
                url = html.escape(opp.get("url", MYIMPACTPAGE_OPPORTUNITIES_URL))
                row = "<tr>"
                if i == 0:
                    row += f'<td style="border: 1px solid #ddd; padding: 8px;" rowspan="{len(shifts)}">{date_escaped}</td>'
                row += f'<td style="border: 1px solid #ddd; padding: 8px;">{name}</td>'
                row += f'<td style="border: 1px solid #ddd; padding: 8px;">{start_time}</td>'
                row += (
                    f'<td style="border: 1px solid #ddd; padding: 8px;">{end_time}</td>'
                )
                row += f'<td style="border: 1px solid #ddd; padding: 8px;">{open_slots}</td>'
                row += f'<td style="border: 1px solid #ddd; padding: 8px;"><a href="{url}" target="_blank">Sign Up</a></td>'
                row += "</tr>"
                table_rows += row

        return f"""
        <h2>Central Park Private Volunteering (MyImpactPage)</h2>
        <table style="width:100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Date</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Opportunity</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Start Time</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">End Time</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Open Slots</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Link</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        <p><a href="{MYIMPACTPAGE_OPPORTUNITIES_URL}" target="_blank">View all opportunities on MyImpactPage</a></p>
        """

    def _generate_error_html(self) -> str:
        return (
            "<h3>Central Park Private Volunteering</h3>"
            "<p>Unable to retrieve opportunities at this time. "
            "Check that MyImpactPage credentials are configured in AWS Secrets Manager.</p>"
        )


# c = CentralParkPrivateVolunteeringBot()
# print(c.scrape_data_and_return_email_html())

# def parse_sort_key(date_str: str):
#     """Parse date for sorting. Returns (datetime, original) - unparseable go last."""
#     for fmt in (
#         "%A, %B %d, %Y",
#         "%m/%d/%Y",
#         "%m/%d/%y",
#         "%Y-%m-%d",
#         "%B %d, %Y",
#     ):
#         try:
#             return (datetime.strptime(date_str.strip(), fmt), date_str)
#         except ValueError:
#             continue
#     return (datetime.max, date_str)
# print(parse_sort_key("Saturday, August 12, 2023"))
