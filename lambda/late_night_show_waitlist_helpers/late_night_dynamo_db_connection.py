import boto3
from late_night_show_waitlist_helpers.late_night_web_scraper import WaitlistEntry

LATE_NIGHT_WAITLIST_TABLE_NAME = "bethpage-black-bot-late-night-show-waitlists"

class LateNightShowDynamoDBConnection:
	def __init__(self):
		self.dynamodb = boto3.resource("dynamodb")
		self.waitlist_table = self.dynamodb.Table(LATE_NIGHT_WAITLIST_TABLE_NAME)

	def update_waitlist_for_show(self, show_name, waitlist_items):
		print(f'Updating waitlist entries for {show_name}')
		current_item = self.get_show_object_from_db(show_name)
		waitlist_items_for_db = [item.to_dynamo_db_item() for item in waitlist_items]
		current_item["Waitlists"] = waitlist_items_for_db

		self.waitlist_table.put_item(Item=current_item)

	def get_show_object_from_db(self, show_name):
		response = self.waitlist_table.get_item(Key={"id": show_name})
		if "Item" not in response:
			print(f"No object with id={show_name} found... creating one")
			return {'id': show_name}

		return response.get('Item')

	def get_show_waitlist_entries_from_db(self, show_name):
		response = self.waitlist_table.get_item(Key={"id": show_name})
		if "Item" not in response:
			print(f"No object with id={show_name} found... returning empty list")
			return []

		return [WaitlistEntry.from_dynamo_db_item(show_name, item) for item in response.get('Item')['Waitlists']]


# d = DynamoDBConnection()
# REPLACE THIS
# r = d.get_all_emails_list()
# print(r)
# d.add_email_to_all_emails_list("my-new-email@gmail.com")
# r2 = d.get_all_emails_list()
# print(r2)
# print(d.get_all_teetimes())
