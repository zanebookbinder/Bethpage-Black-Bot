"""
Central Park private volunteering bot - scrapes MyImpactPage/Better Impact
for volunteer opportunities with space available (login required).
"""

import html
from collections import defaultdict

from daily_update_helpers.myimpactpage_web_scraper import MyImpactPageWebScraper
from daily_update_helpers.daily_updates_secret_handler import DailyUpdateSecretHandler


OPPORTUNITIES_URL = "https://app.betterimpact.com/Volunteer/Schedule/Opportunities"


class CentralParkPrivateVolunteeringBot:
    """Scrapes Central Park private volunteering opportunities from MyImpactPage."""

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

        print(f"Found {len(opportunities)} shift(s) with space available")

        # Group by date (date on left, grouped)
        by_date = defaultdict(list)
        for opp in opportunities:
            by_date[opp.get("date", "")].append(opp)

        table_rows = ""
        for date in sorted(by_date.keys()):
            shifts = by_date[date]
            date_escaped = html.escape(date)
            for i, opp in enumerate(shifts):
                name = html.escape(opp.get("name", "Opportunity"))
                start_time = html.escape(opp.get("start_time", ""))
                end_time = html.escape(opp.get("end_time", ""))
                open_slots = html.escape(opp.get("open_slots", ""))
                url = html.escape(opp.get("url", OPPORTUNITIES_URL))
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
        <p>Opportunities with space available:</p>
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
        <p><a href="{OPPORTUNITIES_URL}" target="_blank">View all opportunities on MyImpactPage</a></p>
        """

    def _generate_error_html(self) -> str:
        return (
            "<h3>Central Park Private Volunteering</h3>"
            "<p>Unable to retrieve opportunities at this time. "
            "Check that MyImpactPage credentials are configured in AWS Secrets Manager.</p>"
        )


# c = CentralParkPrivateVolunteeringBot()
# print(c.scrape_data_and_return_email_html())
