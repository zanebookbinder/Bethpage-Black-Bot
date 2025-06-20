import boto3
import json


class SecretHandler:

    def get_bethpage_username_and_password():
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
        password = secret.get("bethpage_password")
        return username, password

    def get_sender_email():
        secret_name = "bethpage-sender-email-secret"
        region_name = "us-east-1"

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)

        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        secret_string = get_secret_value_response["SecretString"]
        secret = json.loads(secret_string)

        # Extract username and password
        return secret.get("sender_email")