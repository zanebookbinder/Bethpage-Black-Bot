import logging
import boto3
from daily_update_helpers.late_night_web_scraper import WaitlistEntry

logger = logging.getLogger(__name__)

DAILY_UPDATES_TABLE_NAME = "daily-updates-data"

class DailyUpdateDynamoDbConnection:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.daily_updates_table = self.dynamodb.Table(DAILY_UPDATES_TABLE_NAME)

    def update_waitlist_for_show(self, show_name, waitlist_items):
        logger.debug("Updating %d waitlist entries for %s", len(waitlist_items), show_name)
        current_item = self.get_show_object_from_db(show_name)
        waitlist_items_for_db = [item.to_dynamo_db_item() for item in waitlist_items]
        current_item["Waitlists"] = waitlist_items_for_db

        self.daily_updates_table.put_item(Item=current_item)

    def update_volunteering_for_org(self, org_name, opportunities):
        """Store volunteering opportunities under the given org id.
        `opportunities` should be a list of dicts serializable to DynamoDB.
        """
        logger.debug("Updating %d volunteering opportunities for %s", len(opportunities), org_name)
        current_item = self.get_show_object_from_db(org_name)
        current_item["Volunteering Opportunities"] = opportunities
        self.daily_updates_table.put_item(Item=current_item)

    def get_show_object_from_db(self, show_name):
        response = self.daily_updates_table.get_item(Key={"id": show_name})
        if "Item" not in response:
            logger.debug("No DynamoDB object found for %s, creating new one", show_name)
            return {"id": show_name}

        return response.get("Item")

    def get_show_waitlist_entries_from_db(self, show_name):
        response = self.daily_updates_table.get_item(Key={"id": show_name})
        if "Item" not in response:
            logger.debug("No waitlist entries found for %s", show_name)
            return []

        return [
            WaitlistEntry.from_dynamo_db_item(show_name, item)
            for item in response.get("Item")["Waitlists"]
        ]

    def get_volunteering_for_org(self, org_name):
        response = self.daily_updates_table.get_item(Key={"id": org_name})
        if "Item" not in response:
            logger.debug("No volunteering opportunities found for %s", org_name)
            return []

        item = response.get("Item")
        return item.get("Volunteering Opportunities", [])


# d = DynamoDBConnection()
# REPLACE THIS
# r = d.get_all_emails_list()
# print(r)
# d.add_email_to_all_emails_list("my-new-email@gmail.com")
# r2 = d.get_all_emails_list()
# print(r2)
# print(d.get_all_teetimes())
