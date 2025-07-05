import uuid
import boto3
from lambda_helpers.email_sender import EmailSender
from datetime import datetime, timedelta, timezone

ONE_TIME_LINKS_TABLE_NAME = "bethpage-black-bot-one-time-links"
EXPIRE_TIME_KEY = "expire_time"


class OneTimeLinkHandler:

    def __init__(self, expire_minutes=60):
        self.expire_minutes = expire_minutes
        self.dynamodb = boto3.resource("dynamodb")
        self.one_time_link_table = self.dynamodb.Table(ONE_TIME_LINKS_TABLE_NAME)
        self.email_sender = EmailSender()

    def generate_one_time_link(self, email):
        guid = str(uuid.uuid4())
        expire_time = (
            datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        ).isoformat()

        return {"id": guid, "email": email, EXPIRE_TIME_KEY: expire_time}

    def handle_one_time_link_creation(self, email):
        one_time_link_object = self.generate_one_time_link(email)
        guid = one_time_link_object['id']
        result = self.one_time_link_table.put_item(Item=one_time_link_object)
        self.email_sender.send_one_time_link_email(email, guid)
        return result

    def validate_one_time_link_and_get_email(self, guid):
        try:
            response = self.one_time_link_table.get_item(Key={"id": guid})
            item = response.get("Item")

            if not item:
                return False, "One time link doesn't exist"  # UUID does not exist

            expire_time_str = item.get(EXPIRE_TIME_KEY)
            if not expire_time_str:
                return False, "Expire time doesn't exist"  # Missing expiration time

            expire_time = datetime.fromisoformat(expire_time_str)
            now = datetime.now(timezone.utc)

            if expire_time > now:
                return True, item.get("email")
            else:
                return False, "One time link is expired"  # Expired

        except Exception as e:
            print(f"Error checking UUID in DynamoDB: {e}")
            return False, f"Unknown error: {e}"
