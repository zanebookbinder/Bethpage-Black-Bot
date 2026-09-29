import logging
from daily_update_helpers.daily_updates_dynamo_db_connection import (
    DailyUpdateDynamoDbConnection,
)
from daily_update_helpers.late_night_web_scraper import (
    LateNightWebScraper,
    URL_TO_SHOW_NAME_DICT,
)
from daily_update_helpers.last_week_tonight_web_scraper import (
    LastWeekTonightWebScraper,
    TicketStatus,
)
import traceback
from daily_update_helpers.daily_updates_email_service import (
    DailyUpdateEmailService,
)

logger = logging.getLogger(__name__)


class LateNightShowBot:

    def notify_if_new_waitlist_opportunities(self, verbose=False):
        logger.info("Starting late night show waitlist scrape")

        try:
            # Build the email HTML but do not send (daily_updates_email_service will send)
            body_html = self.scrape_data_and_return_email_html(verbose)
            return body_html

        except Exception as e:
            logger.error("Error in late night show bot: %s", str(e), exc_info=True)
            error_message = traceback.format_exc()
            DailyUpdateEmailService().send_error_email(error_message)
            raise e

    def add_current_waitlists_to_db_and_return_current_items(self, verbose):
        web_scraper = LateNightWebScraper()
        daily_updates_dynamo_db_connection = DailyUpdateDynamoDbConnection()

        try:
            current_waitlist_entries = web_scraper.find_all_available_waitlists()

            for show_name, entries in current_waitlist_entries.items():
                logger.info("Found %d waitlist entries for %s", len(entries), show_name)
                daily_updates_dynamo_db_connection.update_waitlist_for_show(
                    show_name, entries
                )

            return current_waitlist_entries

        except Exception as e:
            logger.error("Error scraping late night ticket site: %s", str(e), exc_info=True)
            raise e
        finally:
            web_scraper.close()

    def scrape_data_and_return_email_html(self, verbose=False):
        """Scrape late-night shows, update DB, and return HTML string for new entries."""
        current_entries = self.add_current_waitlists_to_db_and_return_current_items(
            verbose
        )

        # Commenting this out to send all entries for now
        # filtered = self.filter_entries_for_time(current_entries)

        filtered = current_entries

        john_oliver_entries = self.scrape_john_oliver_entries()

        if not filtered and not john_oliver_entries:
            return None

        return self.build_waitlist_html(filtered, john_oliver_entries)

    def scrape_john_oliver_entries(self):
        """Scrape lastweektickets.com for John Oliver taping availability.

        Returns [] on any failure so a scraping issue there never blocks the
        rest of the late night email section.
        """
        scraper = LastWeekTonightWebScraper()
        try:
            entries = scraper.find_available_and_upcoming_tapings()
            logger.info("Found %d Last Week Tonight entries", len(entries))
            return entries
        except Exception as e:
            logger.error(
                "Error scraping Last Week Tonight tickets: %s", str(e), exc_info=True
            )
            return []
        finally:
            scraper.close()

    def build_waitlist_html(self, new_waitlist_dict, john_oliver_entries=None) -> str:
        """Return the HTML body for late night waitlists and optional volunteer opportunities."""
        html_lines = [
            "<div>",
            "<h2>Late Night Show Waitlists</h2>",
        ]

        if john_oliver_entries:
            html_lines.append(self.build_john_oliver_html(john_oliver_entries))

        if new_waitlist_dict:
            html_lines += [
                "<table style='width: auto; border-collapse: collapse;'>",
                "<thead><tr style='background-color: #f0f0f0;'><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Show Name</th><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Date</th><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Time</th><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Button Text Found</th></tr></thead>",
                "<tbody>",
            ]

            for show_name, entries in new_waitlist_dict.items():
                show_url = [
                    key
                    for key, value in URL_TO_SHOW_NAME_DICT.items()
                    if value == show_name
                ][0]

                for i, entry in enumerate(entries):
                    row = "<tr style='border: 1px solid #ddd;'>"
                    if i == 0:
                        row += f"<td style='border: 1px solid #ddd; padding: 8px;' rowspan='{len(entries)}'>{show_name}<br/>{show_url}</td>"
                    row += f"<td style='border: 1px solid #ddd; padding: 8px;'>{entry.date}</td><td style='border: 1px solid #ddd; padding: 8px;'>{entry.show_time}</td><td style='border: 1px solid #ddd; padding: 8px;'>{entry.button_text}</td>"
                    row += "</tr>"
                    html_lines.append(row)

            html_lines += ["</tbody></table><h4>https://1iota.com/</h4>"]

        html_lines.append("</div>")

        # wrap and return
        return "".join(["<html><body>"] + html_lines + ["</body></html>"])

    def build_john_oliver_html(self, entries) -> str:
        """Return the HTML table for Last Week Tonight with John Oliver ticket availability."""
        html_lines = [
            "<h3>Last Week Tonight with John Oliver</h3>",
            "<table style='width: auto; border-collapse: collapse;'>",
            "<thead><tr style='background-color: #f0f0f0;'><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Date</th><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Status</th><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Details</th></tr></thead>",
            "<tbody>",
        ]

        for entry in entries:
            status_label = (
                "Request Tickets"
                if entry.status == TicketStatus.AVAILABLE
                else "Not Yet Released"
            )
            html_lines.append(
                f"<tr style='border: 1px solid #ddd;'><td style='border: 1px solid #ddd; padding: 8px;'>{entry.date_text}</td><td style='border: 1px solid #ddd; padding: 8px;'>{status_label}</td><td style='border: 1px solid #ddd; padding: 8px;'>{entry.detail}</td></tr>"
            )

        html_lines += ["</tbody></table><h4>https://www.lastweektickets.com/</h4>"]

        return "".join(html_lines)

    def filter_entries_for_time(self, entries_dict):
        # This is a hack to avoid converting the time string to a datetime... oops
        # Filters the list to any times after 4:00pm
        # Sorry not sorry
        new_filtered_entries_dict = {}
        for show_name, entries in entries_dict.items():
            filtered_entries = [e for e in entries if int(e.show_time.strip()[0]) > 3]
            if filtered_entries:
                new_filtered_entries_dict[show_name] = filtered_entries

        return new_filtered_entries_dict


# l = LateNightShowBot()
# l.notify_if_new_waitlist_opportunities(True)
