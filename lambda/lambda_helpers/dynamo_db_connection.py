import boto3
from datetime import datetime
from bbb_config import BethpageBlackBotConfig

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
    
    def get_latest_filtered_tee_times(self):
        response = self.table.get_item(Key = {'id': LATEST_TEE_TIMES_OBJECT_ID})
        if "Item" not in response:
            print(f"No object containing all user emails found")
            return None
        
        user_to_filtered_tee_times_dict = response.get('Item')['filtered_tee_times']
        return user_to_filtered_tee_times_dict
    
    def get_latest_tee_times_all(self):
        response = self.table.get_item(
            Key={
                'id': 'latest-tee-times'
            }
        )
        return response.get('Item')['all_tee_times']

    def get_config(self):
        response = self.table.get_item(
            Key={
                'id': 'config'
            }
        )
        return response.get('Item')['data']

    def update_config_from_json(self, new_config_json):
        # Fetch existing config
        response = self.table.get_item(Key={"id": "config"})
        item = response.get("Item")

        item['data'] = new_config_json

        # Save updated config back to DynamoDB
        result = self.table.put_item(Item=item)
        return result
    
    def get_all_emails_list(self):
        response = self.config_table.get_item(Key = {'id': CONFIG_TABLE_ALL_EMAILS_ID})
        if "Item" not in response:
            print(f"No object containing all user emails found")
            return None
        return response.get('Item')['emails'] # list of emails as strings
    
    def add_email_to_all_emails_list(self, new_email):
        current_list = self.get_all_emails_list()
        updated_emails_object = {'id': CONFIG_TABLE_ALL_EMAILS_ID, 'emails': current_list + [new_email]}
        result = self.config_table.put_item(Item=updated_emails_object)
        return result
    
    def get_user_config(self, email):
        response = self.config_table.get_item(Key={"id": email})
        if "Item" not in response:
            print(f"No config found for user {email}")
            return None
        item = response.get("Item")
        return item
    
    def create_or_update_user_config(self, user_email, new_config=None):
        config_object = BethpageBlackBotConfig(new_config) # uses defaults if new_config is none
        db_item = config_object.config_to_dynamodb_item(user_email)

        result1 = self.config_table.put_item(Item=db_item)
        result2 = self.add_email_to_all_emails_list(user_email)

        return (result1, result2)


# d = DynamoDBConnection()
# r = d.get_all_emails_list()
# print(r)
# d.add_email_to_all_emails_list("my-new-email@gmail.com")
# r2 = d.get_all_emails_list()
# print(r2)
# print(d.get_all_teetimes())