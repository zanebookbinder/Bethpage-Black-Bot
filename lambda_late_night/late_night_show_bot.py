from late_night_show_helpers.late_night_dynamo_db_connection import (
    LateNightShowDynamoDBConnection,
)
from late_night_show_helpers.late_night_email_sender import LateNightEmailSender
from late_night_show_helpers.late_night_web_scraper import (
    LateNightWebScraper,
)
import traceback


class LateNightShowBot:

    def notify_if_new_waitlist_opportunities(self, verbose=False):
        print("Starting late night show waitlist notification process")

        late_night_email_sender = LateNightEmailSender()
        try:
            # Find available waitlists
            new_waitlist_entries = (
                self.add_current_waitlists_to_db_and_return_new_items(verbose)
            )

            filtered_waitlist_entries = self.filter_entries_for_time(new_waitlist_entries)

            if not filtered_waitlist_entries:
                print("No new waitlist opportunities found after filtering. Exiting...")
                return

            print(f"Found new entries for {len(filtered_waitlist_entries)} shows!")

            late_night_email_sender.send_waitlist_email(filtered_waitlist_entries)
            print("Sent email notification!")

        except Exception as e:
            print("Exception:", e)
            error_message = (
                traceback.format_exc()
            )  # Get the full stack trace as a string
            late_night_email_sender.send_error_email(error_message)
            raise e

    def add_current_waitlists_to_db_and_return_new_items(self, verbose):
        web_scraper = LateNightWebScraper()
        late_night_dynamo_db_connection = LateNightShowDynamoDBConnection()

        try:
            # Scrape the 1iota.com site for waitlist opportunities
            current_waitlist_entries = web_scraper.find_all_available_waitlists()

            new_entries_to_alert = {}
            # Log the waitlist entries found
            for show_name, entries in current_waitlist_entries.items():
                existing_waitlist_items_in_db = (
                    late_night_dynamo_db_connection.get_show_waitlist_entries_from_db(
                        show_name
                    )
                )
                existing_waitlist_items_as_str = [
                    str(s) for s in existing_waitlist_items_in_db
                ]
                if verbose:
                    print(
                        "Current waitlist items in db:\n"
                        + ", ".join(existing_waitlist_items_as_str)
                    )
                    print(f"Newly found waitlist items:\n" + ", ".join([str(s) for s in entries]))
                for entry in entries:
                    if str(entry) not in existing_waitlist_items_as_str:
                        if show_name not in new_entries_to_alert:
                            new_entries_to_alert[show_name] = []
                        new_entries_to_alert[show_name].append(entry)

                late_night_dynamo_db_connection.update_waitlist_for_show(
                    show_name, entries
                )

            return new_entries_to_alert

        except Exception as e:
            print(f"Error in check_late_night_ticket_site: {e}")
            raise e
        finally:
            web_scraper.close()

    def filter_entries_for_time(self, entries_dict):
        # This is a hack to avoid converting the time string to a datetime... oops
        # Sorry not sorry
        for show_name, entries in entries_dict.items():
            entries_dict[show_name] = [e for e in entries
                                  if int(e.show_time.strip()[0]) > 3]
            
        return entries_dict

# l = LateNightShowBot()
# l.notify_if_new_waitlist_opportunities(True)
