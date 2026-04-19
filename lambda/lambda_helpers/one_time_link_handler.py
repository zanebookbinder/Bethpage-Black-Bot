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

    def generate_one_time_link(self, email, is_pause=False):
        guid = str(uuid.uuid4())
        expire_time = (
            datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        ).isoformat()

        item = {"id": guid, "email": email, EXPIRE_TIME_KEY: expire_time}
        if is_pause:
            item["pause"] = True
        return item

    def generate_and_store_link(self, email, is_pause=False):
        """Generate a one-time link, persist it to DynamoDB, and return the GUID.
        Does NOT send an email — callers embed the GUID in their own emails."""
        link_obj = self.generate_one_time_link(email, is_pause=is_pause)
        self.one_time_link_table.put_item(Item=link_obj)
        logger.debug("Stored one-time link for %s (expires %s)", email, link_obj[EXPIRE_TIME_KEY])
        return link_obj["id"]

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
        """Returns (is_valid, email_or_error, is_pause)."""
        try:
            response = self.one_time_link_table.get_item(Key={"id": guid})
            item = response.get("Item")

            if not item:
                return False, "One time link doesn't exist", False

            is_valid, email_or_error = self.is_one_time_link_valid(item)
            is_pause = item.get("pause", False) if is_valid else False
            return is_valid, email_or_error, is_pause

        except Exception as e:
            logger.error("Error validating one-time link: %s", str(e))
            return False, f"Unknown error: {e}", False

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