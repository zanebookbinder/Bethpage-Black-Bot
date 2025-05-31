import boto3
from datetime import datetime
from decimal import Decimal
import json

class DynamoDBConnection:

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table("tee-times")

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
    
    def to_json_str(self, data):
        return json.dumps(data, default=self.decimal_default)
    
    def decimal_default(self, obj):
        if isinstance(obj, Decimal):
            # Convert to int if whole number, else float
            return int(obj) if obj % 1 == 0 else float(obj)
        raise TypeError(f"Type {type(obj)} not serializable")


# d = DynamoDBConnection()
# print(d.get_all_teetimes())