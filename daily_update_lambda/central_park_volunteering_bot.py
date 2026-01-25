import requests
from bs4 import BeautifulSoup


class CentralParkVolunteeringBot:
    def __init__(self):
        self.url = "https://www.centralparknyc.org/volunteer/community-volunteer-days"
        self.session = requests.Session()

    def scrape_data_and_return_email_html(self):
        print('Starting Central Park volunteering community day notification process')
        try:
            response = self.session.get(self.url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Find the upcoming events container
            events_section = soup.find(
                "h2", string=lambda s: s and "Upcoming Events" in s
            )
            if not events_section:
                return self._generate_no_events_html()

            events_list = events_section.find_next("ul")
            if not events_list:
                return self._generate_no_events_html()

            available_events = []
            for li in events_list.find_all("li", recursive=False):
                date_elem = li.find("h3")
                if not date_elem:
                    continue

                date = date_elem.get_text(strip=True)
                time_links = li.find_all("a", {"data-ticket-link": True})

                for link in time_links:
                    # Check if "Sold Out" is present in the link
                    sold_out_span = link.find(
                        "span", string=lambda s: s and "Sold Out" in s
                    )
                    if not sold_out_span:
                        time = link.get_text(strip=True).split("\n")[0]
                        href = link.get("href", "#")
                        available_events.append(
                            {"date": date, "time": time, "link": href}
                        )

            return self._generate_email_html(available_events)

        except Exception as e:
            print(f"Error scraping Central Park volunteering: {e}")
            return self._generate_error_html()

    def _generate_email_html(self, events):
        if not events:
            return "<h3>Central Park Community Days</h3><p>No available volunteering opportunities at this time.</p>"

        print(f'Found {len(events)} events')
        table_rows = ""
        for event in events:
            table_rows += f"""
            <tr>
                <td>{event['date']}</td>
                <td>{event['time']}</td>
                <td><a href="{event['link']}" target="_blank">Register</a></td>
            </tr>
            """

        return f"""
        <h3>Central Park Community Days</h3>
        <table style="width:100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Date</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Time</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Link</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        """

    def _generate_no_events_html(self):
        return "<h3>Central Park Volunteering</h3><p>No upcoming events found.</p>"

    def _generate_error_html(self):
        return "<h3>Central Park Volunteering</h3><p>Unable to retrieve volunteering opportunities at this time.</p>"


# c = CentralParkVolunteeringBot()
# print(c.scrape_data_and_return_email_html())
