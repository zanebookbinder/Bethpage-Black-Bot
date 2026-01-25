from daily_update_helpers.daily_updates_dynamo_db_connection import (
    DailyUpdateDynamoDbConnection,
)
from daily_update_helpers.late_night_web_scraper import (
    LateNightWebScraper,
    URL_TO_SHOW_NAME_DICT,
)
import traceback
from daily_update_helpers.daily_updates_email_service import (
    DailyUpdateEmailService,
)


class LateNightShowBot:

    def notify_if_new_waitlist_opportunities(self, verbose=False):
        print("Starting late night show waitlist notification process")

        try:
            # Build the email HTML but do not send (daily_updates_email_service will send)
            body_html = self.scrape_data_and_return_email_html(verbose)
            return body_html

        except Exception as e:
            print("Exception:", e)
            error_message = traceback.format_exc()
            # use the email sender to notify of errors
            DailyUpdateEmailService().send_error_email(error_message)
            raise e

    def add_current_waitlists_to_db_and_return_current_items(self, verbose):
        web_scraper = LateNightWebScraper()
        daily_updates_dynamo_db_connection = DailyUpdateDynamoDbConnection()

        try:
            # Scrape the 1iota.com site for waitlist opportunities
            current_waitlist_entries = web_scraper.find_all_available_waitlists()

            # Log the waitlist entries found
            for show_name, entries in current_waitlist_entries.items():
                existing_waitlist_items_in_db = daily_updates_dynamo_db_connection.get_show_waitlist_entries_from_db(
                    show_name
                )
                existing_waitlist_items_as_str = [
                    str(s) for s in existing_waitlist_items_in_db
                ]
                if verbose:
                    print(
                        "Current waitlist items in db:\n"
                        + ", ".join(existing_waitlist_items_as_str)
                    )
                    print(
                        f"Newly found waitlist items:\n"
                        + ", ".join([str(s) for s in entries])
                    )

                daily_updates_dynamo_db_connection.update_waitlist_for_show(
                    show_name, entries
                )

            return current_waitlist_entries

        except Exception as e:
            print(f"Error in check_late_night_ticket_site: {e}")
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

        if not filtered:
            return None

        return self.build_waitlist_html(filtered)

    def build_waitlist_html(self, new_waitlist_dict) -> str:
        """Return the HTML body for late night waitlists and optional volunteer opportunities."""
        html_lines = [
            "<div>",
            "<h2>Late Night Show Waitlists</h2>",
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

        # wrap and return
        return "".join(["<html><body>"] + html_lines + ["</body></html>"])

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
