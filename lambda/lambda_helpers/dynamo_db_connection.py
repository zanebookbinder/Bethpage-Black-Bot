import boto3
from datetime import datetime
from lambda_helpers.bethpage_black_config import BethpageBlackBotConfig

TEE_TIMES_TABLE_NAME = "tee-times"
CONFIG_TABLE_NAME = "bethpage-black-bot-config"
CONFIG_TABLE_ALL_EMAILS_ID = "all-emails"
LATEST_TEE_TIMES_OBJECT_ID = "latest-tee-times"
ALL_TEE_TIMES_OBJECT_ID = "all_tee_times"
FILTERED_TEE_TIMES_OBJECT_ID = "filtered_tee_times"

class DynamoDBConnection:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(TEE_TIMES_TABLE_NAME)
        self.config_table = self.dynamodb.Table(CONFIG_TABLE_NAME)

    def publish_teetimes(self, all_tee_times, filtered_tee_times):
        item = {
            "id": datetime.now().isoformat(),
            ALL_TEE_TIMES_OBJECT_ID: all_tee_times,
            FILTERED_TEE_TIMES_OBJECT_ID: filtered_tee_times,
        }
        self.table.put_item(Item=item)

        # Update the "latest-tee-times" item with the same data (except id)
        latest_item = {
            "id": LATEST_TEE_TIMES_OBJECT_ID,
            ALL_TEE_TIMES_OBJECT_ID: all_tee_times,
            FILTERED_TEE_TIMES_OBJECT_ID: filtered_tee_times,
        }
        self.table.put_item(Item=latest_item)
        return item["id"]
    
    def get_latest_tee_times_object(self):
        response = self.table.get_item(Key = {'id': LATEST_TEE_TIMES_OBJECT_ID})
        if "Item" not in response:
            print(f"No object with id={LATEST_TEE_TIMES_OBJECT_ID} found")
            return None
        return response.get('Item')
    
    def get_latest_filtered_tee_times(self):
        filtered_tee_times = self.get_latest_tee_times_object()[FILTERED_TEE_TIMES_OBJECT_ID]
        return filtered_tee_times
    
    def get_latest_tee_times_all(self):
        all_tee_times = self.get_latest_tee_times_object()[ALL_TEE_TIMES_OBJECT_ID]
        return all_tee_times
    
    def get_all_emails_list(self):
        response = self.config_table.get_item(Key = {'id': CONFIG_TABLE_ALL_EMAILS_ID})
        if "Item" not in response:
            print(f"No object with id={CONFIG_TABLE_ALL_EMAILS_ID} found")
            return None
        return response.get('Item')['emails'] # list of emails as strings
    
    def add_email_to_all_emails_list(self, new_email):
        current_list = self.get_all_emails_list()
        if new_email in current_list:
            print(f"Email is already in list. New email: {new_email}, List: {current_list}")
            return False, "Email is already in list"
        
        updated_emails_object = {'id': CONFIG_TABLE_ALL_EMAILS_ID, 'emails': current_list + [new_email]}
        self.config_table.put_item(Item=updated_emails_object)
        return True, ""
    
    def get_user_config(self, email):
        response = self.config_table.get_item(Key={"id": email})
        if "Item" not in response:
            print(f"No config object found for user {email}")
            return None
        item = response.get("Item")
        return item
    
    def create_or_update_user_config(self, user_email, new_config=None):
        config_object = BethpageBlackBotConfig(new_config) # uses defaults if new_config is none
        db_item = config_object.config_to_dynamodb_item(user_email)

        self.config_table.put_item(Item=db_item)


# d = DynamoDBConnection()
# r = d.get_all_emails_list()
# print(r)
# d.add_email_to_all_emails_list("my-new-email@gmail.com")
# r2 = d.get_all_emails_list()
# print(r2)
# print(d.get_all_teetimes())