import boto3
import json

DAILY_UPDATES_SECRET_NAME = "daily-updates-secret"
REGION_NAME = "us-east-1"


class DailyUpdateSecretHandler:

    def get_admin_email():
        secret_name = "bethpage-secret"

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=REGION_NAME)

        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        secret_string = get_secret_value_response["SecretString"]
        secret = json.loads(secret_string)

        # Extract username and password
        username = secret.get("bethpage_email")
        return username

    def get_daily_updates_secret_info():
        # NOTE TO SELF: This API KEY is within the My-First-Project GCP project

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=REGION_NAME)

        get_secret_value_response = client.get_secret_value(
            SecretId=DAILY_UPDATES_SECRET_NAME
        )

        secret_string = get_secret_value_response["SecretString"]
        secret = json.loads(secret_string)
        home_address = secret.get("home-address")
        api_key = secret.get("google-maps-api-key")

        return home_address, api_key

    def get_daily_updates_emails():
        # NOTE TO SELF: This API KEY is within the My-First-Project GCP project

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=REGION_NAME)

        get_secret_value_response = client.get_secret_value(
            SecretId=DAILY_UPDATES_SECRET_NAME
        )

        secret_string = get_secret_value_response["SecretString"]
        secret = json.loads(secret_string)
        emails = [s.strip() for s in secret.get("emails").split(",")]

        return emails

    def get_myimpactpage_credentials():
        """Returns (username, password) for MyImpactPage / Better Impact login."""
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=REGION_NAME)
        get_secret_value_response = client.get_secret_value(
            SecretId=DAILY_UPDATES_SECRET_NAME
        )
        secret_string = get_secret_value_response["SecretString"]
        secret = json.loads(secret_string)

        username = secret.get("myimpactpage-username")
        password = secret.get("myimpactpage-password")
        return username, password


# e = DailyUpdateSecretHandler.get_daily_updates_emails()
# print(e)
