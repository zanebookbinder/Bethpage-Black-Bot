import logging
import uuid
import boto3
from lambda_helpers.email_sender import EmailSender
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

ONE_TIME_LINKS_TABLE_NAME = "bethpage-black-bot-one-time-links"
EXPIRE_TIME_KEY = "expire_time"

class OneTimeLinkHandler:

    def __init__(self, expire_minutes=60):
        self.expire_minutes = expire_minutes
        self.dynamodb = boto3.resource("dynamodb")
        self.one_time_link_table = self.dynamodb.Table(ONE_TIME_LINKS_TABLE_NAME)
        self.email_sender = None

    def generate_one_time_link(self, email):
        guid = str(uuid.uuid4())
        expire_time = (
            datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        ).isoformat()

        return {"id": guid, "email": email, EXPIRE_TIME_KEY: expire_time}

    def handle_one_time_link_creation(self, email, welcome_email=False):
        if not self.email_sender:
            self.email_sender = EmailSender()

        one_time_link_object = self.generate_one_time_link(email)
        logger.debug("Generated one-time link for %s", email)
        guid = one_time_link_object['id']
        self.one_time_link_table.put_item(Item=one_time_link_object)
        self.email_sender.send_one_time_link_email(email, guid, welcome_email)

    def is_one_time_link_valid(self, one_time_link_item):
        expire_time_str = one_time_link_item.get(EXPIRE_TIME_KEY)
        if not expire_time_str:
            return False, "Expire time doesn't exist"  # Missing expiration time

        expire_time = datetime.fromisoformat(expire_time_str)
        now = datetime.now(timezone.utc)

        if expire_time > now:
            return True, one_time_link_item.get("email")
        else:
            return False, "One time link is expired"  # Expired

    def validate_one_time_link_and_get_email(self, guid):
        try:
            response = self.one_time_link_table.get_item(Key={"id": guid})
            item = response.get("Item")

            if not item:
                return False, "One time link doesn't exist"  # UUID does not exist

            return self.is_one_time_link_valid(item)

        except Exception as e:
            logger.error("Error validating one-time link: %s", str(e))
            return False, f"Unknown error: {e}"

    def get_all_link_objects(self):
        all_items = []
        scan_kwargs = {}

        while True:
            response = self.one_time_link_table.scan(**scan_kwargs)
            all_items.extend(response.get("Items", []))

            if "LastEvaluatedKey" in response:
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            else:
                break

        return all_items

    def remove_old_one_time_links(self):
        logger.info("Cleaning up expired one-time links")

        all_link_items = self.get_all_link_objects()
        removed_count = 0
        for item in all_link_items:
            is_link_active, message = self.is_one_time_link_valid(item)
            if not is_link_active:
                self.one_time_link_table.delete_item(Key={"id": item["id"]})
                removed_count += 1

        logger.info("Removed %d expired one-time links", removed_count)

    def one_time_link_to_str(self, one_time_link_item):
        return f"[id={one_time_link_item['id']}, email='{one_time_link_item['email']}',\
        {EXPIRE_TIME_KEY}={one_time_link_item[EXPIRE_TIME_KEY]}]"

# otlh = OneTimeLinkHandler()
# otlh.remove_old_one_time_links()