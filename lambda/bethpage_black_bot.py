import logging
from lambda_helpers.date_handler import now_eastern
from lambda_helpers.dynamo_db_connection import DynamoDBConnection
from lambda_helpers.email_log import EmailLog
from lambda_helpers.email_sender import EmailSender
from lambda_helpers.one_time_link_handler import OneTimeLinkHandler
from lambda_helpers.secret_handler import SecretHandler
from lambda_helpers.tee_time_filterer import TeeTimeFilterer
from lambda_helpers.web_scraper import WebScraper
import traceback

logger = logging.getLogger(__name__)

PAUSE_LINK_EXPIRE_MINUTES = 10080  # 7 days


class BethpageBlackBot:

    def notify_if_new_tee_times(self):
        logger.info("Starting tee time notification process")
        self.bethpage_email, self.bethpage_password = (
            SecretHandler.get_bethpage_username_and_password()
        )
        email_sender = EmailSender()
        otlh = OneTimeLinkHandler(expire_minutes=PAUSE_LINK_EXPIRE_MINUTES)
        email_log = EmailLog()
        run_time = now_eastern()
        try:
            new_times = self.get_new_tee_times()
            for email, new_times_list in new_times.items():
                pause_guid = otlh.generate_and_store_link(email, is_pause=True)
                email_sender.send_email(email, new_times_list, pause_guid=pause_guid)
                self.log_email_sent(email_log, run_time, email, new_times_list)
        except Exception as e:
            logger.error("Error in tee time notification process: %s", str(e), exc_info=True)
            error_message = traceback.format_exc()
            email_sender.send_error_email(error_message)
            raise e

    def log_email_sent(self, email_log, run_time, email, new_times_list):
        """Record the email for the weekly admin report. Never let a logging
        failure stop the remaining notifications from going out."""
        try:
            email_log.record_email_sent(run_time, email, new_times_list)
        except Exception as e:
            logger.error("Failed to log notification email to %s: %s", email, str(e))

    def get_new_tee_times(self):
        web_scraper = WebScraper(self.bethpage_email, self.bethpage_password)
        dynamo_db_connection = DynamoDBConnection()
        tee_time_filterer = TeeTimeFilterer(db_connection=dynamo_db_connection)

        tee_times = web_scraper.get_tee_time_data()
        logger.info("Found %d tee times on website", len(tee_times))

        available_times_by_day = dynamo_db_connection.get_available_times_by_day()
        already_seen = [t for times in available_times_by_day.values() for t in times]

        all_emails = dynamo_db_connection.get_all_emails_list()
        logger.info("Processing tee times for %d users", len(all_emails))

        emails_to_send = {}
        newly_sent = {}  # {date: [tee_times]} accumulates new times across all users this run

        for user_email in all_emails:
            filtered_tee_times = tee_time_filterer.filter_tee_times_for_user(
                tee_times, user_email
            )
            new_tee_times = tee_time_filterer.remove_existing_tee_times(
                filtered_tee_times, already_seen
            )

            if new_tee_times:
                emails_to_send[user_email] = new_tee_times
                logger.info("Found %d new tee times for %s", len(new_tee_times), user_email)
                for t in new_tee_times:
                    newly_sent.setdefault(t["Date"], [])
                    if t not in newly_sent[t["Date"]]:
                        newly_sent[t["Date"]].append(t)

        if newly_sent:
            for date, times in newly_sent.items():
                available_times_by_day.setdefault(date, [])
                for t in times:
                    if t not in available_times_by_day[date]:
                        available_times_by_day[date].append(t)
            dynamo_db_connection.update_available_times_by_day(available_times_by_day)

        dynamo_db_connection.publish_teetimes(tee_times)

        return emails_to_send
