import logging
from lambda_helpers.dynamo_db_connection import DynamoDBConnection
from lambda_helpers.email_sender import EmailSender
from lambda_helpers.secret_handler import SecretHandler
from lambda_helpers.tee_time_filterer import TeeTimeFilterer
from lambda_helpers.web_scraper import WebScraper
import traceback

logger = logging.getLogger(__name__)


class BethpageBlackBot:

    def notify_if_new_tee_times(self):
        logger.info("Starting tee time notification process")
        self.bethpage_email, self.bethpage_password = (
            SecretHandler.get_bethpage_username_and_password()
        )
        email_sender = EmailSender()
        try:
            new_times = self.get_new_tee_times()
            for email, new_times_list in new_times.items():
                email_sender.send_email(email, new_times_list)
        except Exception as e:
            logger.error("Error in tee time notification process: %s", str(e), exc_info=True)
            error_message = traceback.format_exc()
            email_sender.send_error_email(error_message)
            raise e

    def get_new_tee_times(self):
        web_scraper = WebScraper(self.bethpage_email, self.bethpage_password)
        dynamo_db_connection = DynamoDBConnection()
        tee_time_filterer = TeeTimeFilterer()

        tee_times = web_scraper.get_tee_time_data()
        logger.info("Found %d tee times on website", len(tee_times))

        all_emails = dynamo_db_connection.get_all_emails_list()
        logger.info("Processing tee times for %d users", len(all_emails))

        latest_filtered_tee_times_map = (
            dynamo_db_connection.get_latest_filtered_tee_times()
        )

        new_filtered_tee_times_map = {}
        for user_email in all_emails:
            filtered_tee_times = tee_time_filterer.filter_tee_times_for_user(
                tee_times, user_email
            )
            previous_filtered_tee_times = (
                latest_filtered_tee_times_map[user_email]
                if user_email in latest_filtered_tee_times_map
                else []
            )

            new_tee_times = tee_time_filterer.remove_existing_tee_times(
                filtered_tee_times, previous_filtered_tee_times
            )
            if new_tee_times:
                new_filtered_tee_times_map[user_email] = new_tee_times
                logger.info("Found %d new tee times for %s", len(new_tee_times), user_email)

        dynamo_db_connection.publish_teetimes(tee_times, new_filtered_tee_times_map)

        return new_filtered_tee_times_map
