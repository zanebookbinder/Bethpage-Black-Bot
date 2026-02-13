import boto3
import json
from typing import List, Tuple
from daily_update_helpers.daily_update_constants import (
    REGION_NAME,
    DAILY_UPDATES_SECRET_NAME,
    BETHPAGE_SECRET_NAME,
)


class DailyUpdateSecretHandler:
    _secret_cache = {}
    _client = None

    @classmethod
    def _get_client(cls):
        """Reuse a single Secrets Manager client across all calls."""
        if cls._client is None:
            cls._client = boto3.client(service_name="secretsmanager", region_name=REGION_NAME)
        return cls._client

    @classmethod
    def _get_secret(cls, secret_id: str) -> dict:
        """Fetch and cache secrets to avoid duplicate API calls."""
        if secret_id not in cls._secret_cache:
            client = cls._get_client()
            response = client.get_secret_value(SecretId=secret_id)
            cls._secret_cache[secret_id] = json.loads(response["SecretString"])
        return cls._secret_cache[secret_id]

    @classmethod
    def get_admin_email(cls) -> str:
        return cls._get_secret(BETHPAGE_SECRET_NAME).get("bethpage_email")

    @classmethod
    def get_daily_updates_secret_info(cls) -> Tuple[str, str]:
        s = cls._get_secret(DAILY_UPDATES_SECRET_NAME)
        return s.get("home-address"), s.get("google-maps-api-key")

    @classmethod
    def get_daily_updates_emails(cls) -> List[str]:
        s = cls._get_secret(DAILY_UPDATES_SECRET_NAME)
        return [e.strip() for e in (s.get("emails") or "").split(",")]

    @classmethod
    def get_myimpactpage_credentials(cls) -> Tuple[str, str]:
        s = cls._get_secret(DAILY_UPDATES_SECRET_NAME)
        return s.get("myimpactpage-username"), s.get("myimpactpage-password")
