import boto3
from datetime import datetime
from bbb_config import BethpageBlackBotConfig

class DynamoDBConnection:

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table("tee-times")
        self.config_table = self.dynamodb.Table("bethpage-black-bot-config")

    def publish_teetimes(self, all_tee_times, filtered_tee_times):
        item = {
        "id": datetime.now().isoformat(),
        "all_tee_times": all_tee_times,
        "filtered_tee_times": filtered_tee_times,
        }
        self.table.put_item(Item=item)

        # Update the "latest-tee-times" item with the same data (except id)
        latest_item = {
            "id": "latest-tee-times",
            "all_tee_times": all_tee_times,
            "filtered_tee_times": filtered_tee_times,
        }
        self.table.put_item(Item=latest_item)
        return item["id"]
    
    def get_latest_filtered_tee_times(self):
        response = self.table.get_item(
            Key={
                'id': 'latest-tee-times'
            }
        )
        return response.get('Item')['filtered_tee_times']
    
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
    
    def get_user_config(self, email):
        response = self.config_table.get_item(Key={"id": email})
        item = response.get("Item")
        return item
    
    def create_or_update_user_config(self, user_email, new_config=None):
        config_object = BethpageBlackBotConfig(new_config) # uses defaults if new_config is none
        db_item = config_object.config_to_dynamodb_item(user_email)

        result = self.config_table.put_item(Item=db_item)
        return result


# d = DynamoDBConnection()
# print(d.get_all_teetimes())