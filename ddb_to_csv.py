import boto3
import pandas as pd

def dynamodb_to_csv(table_name, csv_filename, region_name='us-west-2'):
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(table_name)

    # Scan the table (handles pagination)
    items = []
    response = table.scan()
    items.extend(response.get('Items', []))
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    if not items:
        print("No items found in the table.")
        return

    # Convert to DataFrame and save as CSV
    df = pd.DataFrame(items)
    df.to_csv(csv_filename, index=False)
    print(f"Exported {len(df)} items to {csv_filename}")

if __name__ == "__main__":
    # Replace with your table name and desired output file
    dynamodb_to_csv('strava-activities', 'strava-activities.csv', region_name='us-west-2')