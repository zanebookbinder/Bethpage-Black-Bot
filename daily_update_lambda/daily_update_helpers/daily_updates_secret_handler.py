import boto3
import json
from daily_update_helpers.daily_update_constants import (
    REGION_NAME,
    DAILY_UPDATES_SECRET_NAME,
    BETHPAGE_SECRET_NAME,
)


class DailyUpdateSecretHandler:

    @staticmethod
    def _get_secret(secret_id: str) -> dict:
        client = boto3.session.Session().client(
            service_name="secretsmanager", region_name=REGION_NAME
        )
        return json.loads(client.get_secret_value(SecretId=secret_id)["SecretString"])

    def get_admin_email():
        return DailyUpdateSecretHandler._get_secret(BETHPAGE_SECRET_NAME).get(
            "bethpage_email"
        )

    def get_daily_updates_secret_info():
        s = DailyUpdateSecretHandler._get_secret(DAILY_UPDATES_SECRET_NAME)
        return s.get("home-address"), s.get("google-maps-api-key")

    def get_daily_updates_emails():
        s = DailyUpdateSecretHandler._get_secret(DAILY_UPDATES_SECRET_NAME)
        return [e.strip() for e in (s.get("emails") or "").split(",")]

    def get_myimpactpage_credentials():
        s = DailyUpdateSecretHandler._get_secret(DAILY_UPDATES_SECRET_NAME)
        return s.get("myimpactpage-username"), s.get("myimpactpage-password")
