import boto3
import json


class SecretHandler:
    _secret_cache = {}
    _client = None

    @classmethod
    def _get_client(cls):
        """Reuse a single Secrets Manager client across all calls."""
        if cls._client is None:
            cls._client = boto3.client(service_name="secretsmanager", region_name="us-east-1")
        return cls._client

    @classmethod
    def _get_secret(cls, secret_name):
        """Fetch and cache secrets to avoid duplicate API calls."""
        if secret_name not in cls._secret_cache:
            client = cls._get_client()
            response = client.get_secret_value(SecretId=secret_name)
            cls._secret_cache[secret_name] = json.loads(response["SecretString"])
        return cls._secret_cache[secret_name]

    @classmethod
    def get_bethpage_username_and_password(cls):
        secret = cls._get_secret("bethpage-secret")
        return secret.get("bethpage_email"), secret.get("bethpage_password")

    @classmethod
    def get_sender_email(cls):
        secret = cls._get_secret("bethpage-sender-email-secret")
        return secret.get("sender_email")

    @classmethod
    def get_one_time_link_sender_email(cls):
        secret = cls._get_secret("bethpage-sender-email-secret")
        return secret.get("one_time_link_email")