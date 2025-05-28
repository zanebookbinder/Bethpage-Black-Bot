import boto3
import uuid

class DynamoDBConnection:

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table("tee-times")

    def publish_teetimes(self, data):
        self.clear_table()
        item = {
            "id": str(uuid.uuid4()),  # generate a unique ID
            "data": data,  # store JSON as a nested map
        }
        self.table.put_item(Item=item)
        return item["id"]

    def get_all_teetimes(self):
        response = self.table.scan()
        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = self.table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        return items
    
    def clear_table(self):
        # Scan all items
        response = self.table.scan()
        items = response.get('Items', [])

        # Delete each item
        with self.table.batch_writer() as batch:
            for item in items:
                key = {
                    'id': item['id'],   # replace 'pk' with your partition key name
                }
                batch.delete_item(Key=key)

# d = DynamoDBConnection()
# print(d.get_all_teetimes())