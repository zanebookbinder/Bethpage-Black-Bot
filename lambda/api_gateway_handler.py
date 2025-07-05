from lambda_helpers.dynamo_db_connection import DynamoDBConnection
from lambda_helpers.email_sender import EmailSender
from lambda_helpers.one_time_link_handler import OneTimeLinkHandler
from decimal import Decimal
import json

class ApiGatewayHandler:
    def __init__(self):
        self.email_sender = EmailSender()

    def handle(self, event):
        try:
            method, path = event["routeKey"].split()
            print(f"API call to route {path} with method {method}")

            response_body = {}
            status_code = 200

            # RETURNS THE USER CONFIG
            if method == "GET" and path == "/config":
                response_body = self.get_config_from_dynamo_db()

            # UPDATES USER CONFIG
            elif method == "POST" and path == "/config":
                result = self.save_config_to_dynamo_db(event)
                response_body = {"message": "Config updated", "result": result}

            # GETS MOST RECENTLY-SCRAPED TEE TIMES
            elif method == "GET" and path == "/getRecentTimes":
                recentTimes = self.get_recent_times_from_db()
                response_body = {"message": "Config retrieved", "result": recentTimes}

            # REGISTERS A NEW USER
            elif method == "POST" and path == "/register":
                result = self.register_new_user(event)
                response_body = {"message": "Registered new user", "result": result}

            # GETS USER CONFIG BASED ON EMAIL
            elif method == "GET" and path == "/getUserConfig":
                config_exists, config = self.get_user_config(event)
                if config_exists:
                    response_body = {
                        "success": True,
                        "message": "Retrieved user config",
                        "result": config,
                    }
                else:
                    response_body = {
                        "success": False,
                        "message": "User config not found",
                        "result": {},
                    }

            # UPDATES USER CONFIG BASED ON EMAIL
            elif method == "POST" and path == "/updateUserConfig":
                result = self.create_or_update_user_config(event)
                response_body = {
                    "message": "Created or updated user config",
                    "result": result,
                }

            # CREATES A ONE TIME LINK AND EMAILS IT TO THE USER
            elif method == "GET" and path == "/createOneTimeLink":
                result = self.create_one_time_link_and_send(event)
                response_body = {
                    "message": "Created one time link and sent to user",
                    "result": result,
                    "success": True
                }

            # VALIDATES THAT A ONE TIME LINK EXISTS AND RETURNS THE USER
            elif method == "GET" and path == "/validateOneTimeLink":
                success, emailOrErrorMessage = self.validate_one_time_link(event)

                if success:
                    response_body = {
                        "message": "Retrieved valid one time link",
                        "email": emailOrErrorMessage,
                        "errorMessage": "",
                    }
                else:
                    response_body = {
                        "message": "Invalid one time link",
                        "email": "",
                        "errorMessage": emailOrErrorMessage,
                    }

            # NO MATCHING ROUTE FOUND
            else:
                response_body = {"error": "Unsupported route"}
                status_code = 404

            return self.get_api_response(response_body, status_code)
        except Exception as e:
            print("ERROR: " + str(e))
            response_body = {"Error during API route processing:", str(e)}
            return self.get_api_response(response_body, 404)

    def get_config_from_dynamo_db(self):
        ddc = DynamoDBConnection()
        return ddc.get_config()

    def save_config_to_dynamo_db(self, event):
        ddc = DynamoDBConnection()
        data = json.loads(event.get("body", "{}"))
        result = ddc.update_config_from_json(data)
        return result

    def get_recent_times_from_db(self):
        ddc = DynamoDBConnection()
        return ddc.get_latest_tee_times_all()

    def register_new_user(self, event):
        ddc = DynamoDBConnection()
        body = json.loads(event.get("body", "{}"))
        email = body.get("email")

        result = ddc.add_email_to_all_emails_list(email)
        result2 = ddc.create_or_update_user_config(email, body)
        result3 = self.email_sender.send_welcome_email(email)

        return [result3]

    def get_user_config(self, event):
        ddc = DynamoDBConnection()
        email = event.get("queryStringParameters", {}).get("email")
        config_or_none = ddc.get_user_config(email)
        return (True, config_or_none) if config_or_none else (False, None)

    def create_or_update_user_config(self, event):
        ddc = DynamoDBConnection()
        config_data = json.loads(event.get("body", "{}"))
        user_email = config_data["email"]
        result = ddc.create_or_update_user_config(user_email, config_data)
        return result

    def create_one_time_link_and_send(self, event):
        # GET THE USER'S EMAIL FROM EVENT
        user_email = event.get("queryStringParameters", {}).get("email")

        # CREATE, SAVE, AND EMAIL THE LINK
        otlh = OneTimeLinkHandler()
        result = otlh.handle_one_time_link_creation(user_email)
        return result
    
    def validate_one_time_link(self, event):
        # GET THE CURRENT GUID
        guid_in_browser = event.get("queryStringParameters", {}).get("guid")

        otlh = OneTimeLinkHandler()
        successAsBool, emailOrErrorMessage = otlh.validate_one_time_link_and_get_email(guid_in_browser)

        print(f"Validated one time link. Success={successAsBool}, Email or error message={emailOrErrorMessage}")
        # result = (True, email) OR (False, error message)
        return successAsBool, emailOrErrorMessage

    def get_api_response(self, body, status_code):
        if not isinstance(body, str):
            body = json.dumps(body, default=self.decimal_default)

        return {
            "statusCode": status_code,
            "body": body,
            "headers": {"Content-Type": "application/json"},
        }

    def decimal_default(self, obj):
        if isinstance(obj, Decimal):
            # Convert to int if whole number, else float
            return int(obj) if obj % 1 == 0 else float(obj)
        raise TypeError(f"Type {type(obj)} not serializable")


# a = ApiGatewayHandler()

# testEvent = {
#   "version": "2.0",
#   "routeKey": "GET /validateOneTimeLink",
#   "rawPath": "/validateOneTimeLink",
#   "rawQueryString": "",
#   "headers": {
#     "content-type": "application/json"
#   },
#   "requestContext": {
#     "http": {
#       "method": "GET",
#       "path": "/validateOneTimeLink"
#     }
#   },
#     "body": "{\"guid\":\"1111234567890\"}",
# #   "body": "{\"email\":\"fakeemail@gmail.com\",\"earliest_playable_time\":\"7:32am\",\"extra_playable_days\":[\"6/20/2025\",\"7/5/2025\"],\"include_holidays\":false,\"minimum_minutes_before_sunset\":7,\"min_players\":3,\"playable_days_of_week\":[\"Friday\",\"Saturday\",\"Tuesday\",\"Wednesday\",\"Monday\",\"Thursday\"]}",
#   "isBase64Encoded": False
# }

# r = a.handle(testEvent)
# print(r)
