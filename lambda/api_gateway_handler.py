from lambda_helpers.dynamo_db_connection import DynamoDBConnection
from lambda_helpers.email_sender import EmailSender
from lambda_helpers.secret_handler import SecretHandler
from decimal import Decimal
import json

class ApiGatewayHandler():
    def __init__(self):
        self.sender_email = SecretHandler.get_sender_email()

    def handle(self, event):
        try:
            method, path = event['routeKey'].split()
            print(f"API call to route {path} with method {method}")

            response_body = {}
            status_code = 200

            if method == "GET" and path == "/config":
                response_body = self.get_config_from_dynamo_db()

            elif method == "POST" and path == "/config":
                result = self.save_config_to_dynamo_db(event)
                response_body = {"message": "Config updated", "result": result}

            elif method == "GET" and path == "/getRecentTimes":
                recentTimes = self.get_recent_times_from_db()
                response_body = {"message": "Config retrieved", "result": recentTimes}

            elif method == "POST" and path == "/register":
                result = self.register_new_user(event)
                response_body = {"message": "Registered new user", "result": result}

            elif method == "GET" and path == "/email":
                config_exists, config = self.get_user_config(event)
                if config_exists:
                    response_body = {"success": True, "message": "Retrieved user config", "result": config}
                else:
                    response_body = {"success": False, "message": "User config not found", "result": {}}

            elif method == "POST" and path == "/updateUserConfig":
                result = self.create_or_update_user_config(event)
                response_body = {"message": "Created or updated user config", "result": result}

            # NO MATCHING ROUTE FOUND
            else:
                response_body = {"error": "Unsupported route"}
                status_code = 404

            return self.get_api_response(response_body, status_code)
        except Exception as e:
            response_body = {"Error during API route processing:", e}
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
        es = EmailSender(self.sender_email)
        body = json.loads(event.get("body", "{}"))
        email = body.get("email")
        
        result = ddc.add_email_to_all_emails_list(email)
        result2 = ddc.create_or_update_user_config(email, body)
        result3 = es.send_welcome_email(email)

        return [result3]

    def get_user_config(self, event):
        ddc = DynamoDBConnection()
        email = event.get("queryStringParameters", {}).get("email")
        config_or_none = ddc.get_user_config(email)
        return (True, config_or_none) if config_or_none else (False, None)
    
    def create_or_update_user_config(self, event):
        ddc = DynamoDBConnection()
        config_data = json.loads(event.get("body", "{}"))
        user_email = config_data['email']
        result = ddc.create_or_update_user_config(user_email, config_data)
        return result

    def get_api_response(self, body, status_code):
        if not isinstance(body, str):
            body = json.dumps(body, default=self.decimal_default)

        return {
            "statusCode": status_code,
            "body": body,
            "headers": {"Content-Type": "application/json"}
        }
    
    def decimal_default(self, obj):
        if isinstance(obj, Decimal):
            # Convert to int if whole number, else float
            return int(obj) if obj % 1 == 0 else float(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
    
a = ApiGatewayHandler()

testEvent = {
  "version": "2.0",
  "routeKey": "POST /register",
  "rawPath": "/register",
  "rawQueryString": "",
  "headers": {
    "content-type": "application/json"
  },
  "requestContext": {
    "http": {
      "method": "POST",
      "path": "/updateUserConfig"
    }
  },
  "body": "{\"email\":\"fakeemail@gmail.com\",\"earliest_playable_time\":\"7:32am\",\"extra_playable_days\":[\"6/20/2025\",\"7/5/2025\"],\"include_holidays\":false,\"minimum_minutes_before_sunset\":7,\"min_players\":3,\"playable_days_of_week\":[\"Friday\",\"Saturday\",\"Tuesday\",\"Wednesday\",\"Monday\",\"Thursday\"]}",
  "isBase64Encoded": False
}

r = a.handle(testEvent)
print(r)