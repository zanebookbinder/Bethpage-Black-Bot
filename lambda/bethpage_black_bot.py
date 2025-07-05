from lambda_helpers.dynamo_db_connection import DynamoDBConnection
from lambda_helpers.email_sender import EmailSender
from lambda_helpers.secret_handler import SecretHandler
from lambda_helpers.tee_time_filterer import TeeTimeFilterer
from lambda_helpers.web_scraper import WebScraper
import traceback


class BethpageBlackBot:

    def notify_if_new_tee_times(self):
        self.bethpage_email, self.bethpage_password = (
            SecretHandler.get_bethpage_username_and_password()
        )
        email_sender = EmailSender()
        try:
            new_times = self.get_new_tee_times()
            for email, new_times_list in new_times.items():
                email_sender.send_email(email, new_times_list)
        except Exception as e:
            print("Exception:", e)
            error_message = (
                traceback.format_exc()
            )  # Get the full stack trace as a string
            email_sender.send_error_email(error_message)
            raise e

    def get_new_tee_times(self):
        web_scraper = WebScraper(self.bethpage_email, self.bethpage_password)
        dynamo_db_connection = DynamoDBConnection()
        tee_time_filterer = TeeTimeFilterer()

        # GET TEE TIME DATA FROM SITE
        tee_times = web_scraper.get_tee_time_data()
        print("All tee times on website:", tee_times)

        # GET ALL EMAILS FROM CONFIG TABLE
        all_emails = dynamo_db_connection.get_all_emails_list()

        # GET LATEST DATA FROM DYNAMO DB
        latest_filtered_tee_times_map = (
            dynamo_db_connection.get_latest_filtered_tee_times()
        )

        # FILTER AND COMPARE TO PREVIOUS FOR EACH USER
        new_filtered_tee_times_map = {}
        for user_email in all_emails:

            # FILTER TEE TIMES ACCORDING TO USER CONFIGURATION
            filtered_tee_times = tee_time_filterer.filter_tee_times_for_user(
                tee_times, user_email
            )
            previous_filtered_tee_times = (
                latest_filtered_tee_times_map[user_email]
                if user_email in latest_filtered_tee_times_map
                else []
            )

            # LIMIT TO TEE TIMES THAT WEREN'T OBSERVED PREVIOUSLY
            new_tee_times = tee_time_filterer.remove_existing_tee_times(
                filtered_tee_times, previous_filtered_tee_times
            )
            if (
                new_tee_times
            ):  # don't need to include the user in the next round if they have no times, it will be brough in as [] (see three lines above)
                new_filtered_tee_times_map[user_email] = new_tee_times

        # PUBLISH NEWEST TIMES TO DB
        dynamo_db_connection.publish_teetimes(tee_times, new_filtered_tee_times_map)

        # {user: [tee_time1, tee_time2]} mappings
        return new_filtered_tee_times_map
