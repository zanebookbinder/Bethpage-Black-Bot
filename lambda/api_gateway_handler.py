from dynamo_db_connection import DynamoDBConnection
import json

class ApiGatewayHandler():
    def handle(self, event):
        print(event['routeKey'])
        method, path = event['routeKey'].split()

        response_body = {}
        status_code = 200

        match (method, path):
            case ("GET", "/config"):
                response_body = self.get_config_from_dynamo_db()

            case ("POST", "/config"):
                result = self.save_config_to_dynamo_db()
                response_body = {"message": "Config updated", "result": result}

            case _:
                response_body = {"error": "Unsupported route"}
                status_code = 404

        return self.get_api_response(response_body, status_code)
            
    def get_config_from_dynamo_db(self):
        ddc = DynamoDBConnection()
        return ddc.to_json_str(ddc.get_config())

    def save_config_to_dynamo_db(self, event):
        ddc = DynamoDBConnection()
        data = json.loads(event.get("body", "{}"))
        result = ddc.update_config_from_json(data)
        return result

    def get_api_response(self, body, status_code):
        if isinstance(body, str):
            body = json.dumps(body)

        return {
            "statusCode": status_code,
            "body": body,
            "headers": {"Content-Type": "application/json"}
        }