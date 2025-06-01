from web_scraper import WebScraper
from dynamo_db_connection import DynamoDBConnection
from secret_handler import SecretHandler
from tee_time_filterer import TeeTimeFilterer
from email_sender import EmailSender
import traceback
import json

CLEAR_TABLE_LOCAL = False

class BethpaigeBlackBot:
    def notify_if_new_tee_times(self):
        secret_handler = SecretHandler()
        self.email, self.password = secret_handler.get_username_and_password()
        email_sender = EmailSender(self.email)
        try:
            new_times = self.get_new_tee_times()
            if new_times:
                email_sender.send_email(new_times)
        except Exception as e:
            print("Exception:", e)
            error_message = (
                traceback.format_exc()
            )  # Get the full stack trace as a string
            email_sender.send_error_email(error_message)
            raise e

    def get_new_tee_times(self):
        web_scraper = WebScraper(self.email, self.password)
        dynamo_db_connection = DynamoDBConnection()
        tee_time_filterer = TeeTimeFilterer()

        # GET TEE TIME DATA FROM SITE
        tee_times = web_scraper.get_tee_time_data()
        filtered_tee_times = tee_time_filterer.filter_tee_times(tee_times)

        # GET STORED DATA IN DYNAMO DB
        latest_stored_times = dynamo_db_connection.get_latest_filtered_tee_times()

        # PUBLISH CURRENT TIMES TO DB
        dynamo_db_connection.publish_teetimes(tee_times, filtered_tee_times)

        # SUBTRACT DB FROM CURRENT SITE
        new_times = self.remove_existing_tee_times(
            filtered_tee_times, latest_stored_times
        )

        return new_times

    def remove_existing_tee_times(self, times_from_site, existing_times):
        print("Existing times in database:", existing_times)

        if existing_times:
            # Sort existing times
            existing_times_set = set(
                tuple(sorted(item.items())) for item in existing_times
            )

            # Find items on current site that aren't in the existing db table
            new_times = [
                item
                for item in times_from_site
                if tuple(sorted(item.items())) not in existing_times_set
            ]
        else:
            print("No existing times. Considering all times as new")
            new_times = times_from_site

        print("New times (to notify about):", new_times)
        return new_times

def lambda_handler(event, context):
    # If the event came from API Gateway (HTTP API)
    print(event)
    if "routeKey" in event:
        print(event['routeKey'])
        method, path = event['routeKey'].split()

        if path == "/config":
            ddc = DynamoDBConnection()
            if method == "GET":
                return {
                    "statusCode": 200,
                    "body": ddc.to_json_str(ddc.get_config()),
                    "headers": {"Content-Type": "application/json"}
                }
            elif method == "POST":
                data = json.loads(event.get("body", "{}"))
                result = ddc.update_config_from_json(data)
                # Save data to DynamoDB or wherever needed
                return {
                    "statusCode": 200,
                    "body": json.dumps({"message": "Config updated", "result": result}),
                    "headers": {"Content-Type": "application/json"}
                }

        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Path from API Gateway not found"}),
            "headers": {"Content-Type": "application/json"}
        }

    # Otherwise, this is a scheduled or direct invocation
    bot = BethpaigeBlackBot()
    bot.notify_if_new_tee_times()

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Tee time check completed."}),
        "headers": {"Content-Type": "application/json"}
    }


    return {"status": "done"}