import boto3
import json

class DailyUpdateSecretHandler:

    def get_admin_email():
        secret_name = "bethpage-secret"
        region_name = "us-east-1"

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)

        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        secret_string = get_secret_value_response["SecretString"]
        secret = json.loads(secret_string)

        # Extract username and password
        username = secret.get("bethpage_email")
        return username
    
    def get_daily_updates_secret_info():
        secret_name = 'daily-updates-secret'
        region_name = "us-east-1"

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)

        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        secret_string = get_secret_value_response["SecretString"]
        secret = json.loads(secret_string)
        home_address = secret.get("home-address")
        api_key = secret.get("google-maps-api-key")

        return home_address, api_key