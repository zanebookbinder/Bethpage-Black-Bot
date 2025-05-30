import boto3
from datetime import datetime

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

    def create_or_update_config(self, new_config):
        # Fetch existing config
        response = self.table.get_item(Key={"id": "config"})
        item = response.get("Item")

        if not item:
            dynamodb_item = new_config.config_to_dynamodb_item()
        else:
            # Merge new_config fields with existing item data
            current_config = self.dynamodb_item_to_config(item)

            # Update fields (overwrite current_config fields with new_config values)
            current_config.earliest_playable_time = new_config.earliest_playable_time
            current_config.extra_playable_days = new_config.extra_playable_days
            current_config.include_holidays = new_config.include_holidays
            current_config.minimum_minutes_before_sunset = (
                new_config.minimum_minutes_before_sunset
            )
            current_config.min_players = new_config.min_players
            current_config.playable_days_of_week = new_config.playable_days_of_week

            dynamodb_item = current_config.config_to_dynamodb_item()

        # Save updated config back to DynamoDB
        self.table.put_item(Item=dynamodb_item)


# d = DynamoDBConnection()
# print(d.get_all_teetimes())