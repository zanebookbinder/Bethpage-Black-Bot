from lambda_helpers.dynamo_db_connection import DynamoDBConnection
from lambda_helpers.email_sender import EmailSender
from lambda_helpers.one_time_link_handler import OneTimeLinkHandler
from decimal import Decimal
import json
import traceback

class ApiGatewayHandler:
    def __init__(self):
        self.email_sender = EmailSender()
        self.verbose = False

    def handle(self, event):
        headers = event.get("headers", {})
        origin = headers.get("origin") or headers.get("Origin")

        if self.verbose:
            print("EVENT", event)
            print("HEADERS", headers)
            print("ORIGIN", origin)

        allowed_origins = ["http://localhost:3000", "https://www.bethpage-black-bot.com"]

        if origin not in allowed_origins:
            return {
                "statusCode": 403,
                "body": "Forbidden: Invalid origin"
            }
        
        try:
            method, path = event["routeKey"].split()
            print(f"API call to route {path} with method {method}")

            response_body = {}
            status_code = 200

            # GETS MOST RECENTLY-SCRAPED TEE TIMES
            if method == "GET" and path == "/getRecentTimes":
                recentTimes = self.get_recent_times_from_db()
                response_body = {"message": "Recent times retrieved", "result": recentTimes}

            # REGISTERS A NEW USER
            elif method == "POST" and path == "/register":
                result = self.register_new_user(event)
                response_body = {"message": "Registered new user", "result": result}

            # GETS USER CONFIG BASED ON EMAIL
            elif method == "POST" and path == "/getUserConfig":
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
            elif method == "POST" and path == "/createOneTimeLink":
                success, result = self.create_one_time_link_and_send(event)
                message = "Created one time link and sent to user" if success else result
                response_body = {
                    "message": message,
                    "result": result,
                    "success": success
                }

            # VALIDATES THAT A ONE TIME LINK EXISTS AND RETURNS THE USER
            elif method == "POST" and path == "/validateOneTimeLink":
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
            traceback.print_exc()
            response_body = {"Error": "Error during API route processing:" + str(e)}
            return self.get_api_response(response_body, 404)

    def get_recent_times_from_db(self):
        ddc = DynamoDBConnection()
        return ddc.get_latest_tee_times_all()

    def register_new_user(self, event):
        ddc = DynamoDBConnection()
        otlh = OneTimeLinkHandler()
        body = json.loads(event.get("body", "{}"))
        email = body.get("email")

        success, message = ddc.add_email_to_all_emails_list(email)
        if not success: 
            return message

        result = ddc.create_or_update_user_config(email, body)
        result2 = otlh.handle_one_time_link_creation(email, True)

        return result2

    def get_user_config(self, event, user_email=None):
        ddc = DynamoDBConnection()
        post_request_body = json.loads(event.get("body", "{}"))
        user_email = user_email if user_email else post_request_body["email"]
        config_or_none = ddc.get_user_config(user_email)
        return (True, config_or_none) if config_or_none else (False, None)

    def create_or_update_user_config(self, event):
        ddc = DynamoDBConnection()
        post_request_body = json.loads(event.get("body", "{}"))
        user_email = post_request_body["email"]
        result = ddc.create_or_update_user_config(user_email, post_request_body)
        return result

    def create_one_time_link_and_send(self, event):
        # GET THE USER'S EMAIL FROM EVENT
        post_request_body = json.loads(event.get("body", "{}"))
        user_email = post_request_body["email"]
        found_user, _ = self.get_user_config(event, user_email)
        if not found_user:
            response_str = f"Tried to get one time link for email that wasn't registered: {user_email}"
            print(response_str)
            return False, response_str

        # CREATE, SAVE, AND EMAIL THE LINK
        otlh = OneTimeLinkHandler()
        result = otlh.handle_one_time_link_creation(user_email)
        return True, result
    
    def validate_one_time_link(self, event):
        # GET THE CURRENT GUID FROM BROWSER
        post_request_body = json.loads(event.get("body", "{}"))
        guid_in_browser = post_request_body["guid"]

        otlh = OneTimeLinkHandler()
        is_link_valid, emailOrErrorMessage = otlh.validate_one_time_link_and_get_email(guid_in_browser)

        print(f"Validated one time link. Success={is_link_valid}, Email or error message={emailOrErrorMessage}")
        # result = (True, email) OR (False, error message)
        return is_link_valid, emailOrErrorMessage

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
