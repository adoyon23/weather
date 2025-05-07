import json
import boto3
from botocore.exceptions import ClientError
import asyncio
from typing import Dict, Any
import os
import logging
from decimal import Decimal

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_dynamodb_client():
    """Initialize and return a DynamoDB client using credentials from ~/.aws/credentials."""
    try:
        # Create a session using the default profile from ~/.aws/credentials
        session = boto3.Session(profile_name='default')
        
        # Get the region from ~/.aws/config
        region = session.region_name or 'us-east-1'
        
        # Create the DynamoDB resource using the session
        return session.resource('dynamodb', region_name=region)
        
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB client: {str(e)}")
        raise

# Initialize DynamoDB client
try:
    dynamodb = get_dynamodb_client()
    # Verify connection by getting caller identity
    boto3.client('sts').get_caller_identity()
    logger.info("Successfully connected to AWS using credentials from ~/.aws/credentials")
except Exception as e:
    logger.error(f"Failed to connect to AWS: {str(e)}")
    dynamodb = None

def convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    return obj

async def get_dynamodb_item(table_name: str, key: Dict[str, Any]) -> str:
    """Retrieve an item from DynamoDB.
    
    Args:
        table_name: Name of the DynamoDB table
        key: Dictionary containing the primary key attributes
            Example: {"id": "123"} or {"partition_key": "pk", "sort_key": "sk"}
    """
    if not dynamodb:
        return "Error: DynamoDB client not initialized. Please check AWS credentials in ~/.aws/credentials"
        
    try:
        # Get the table
        table = dynamodb.Table(table_name)
        
        # Get the item
        response = table.get_item(Key=key)
        print(response)
        # Check if item exists
        if 'Item' not in response:
            return f"No item found with key: {key}"
            
        # Convert Decimal values to float and return the item as a formatted string
        item = convert_decimals(response['Item'])
        return json.dumps(item, indent=2)
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"DynamoDB error: {error_message}")
        return f"Error retrieving item: {error_message}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Error retrieving item: {str(e)}"

async def main():
    # Example usage
    table_name = "identity"  # Replace with your table name
    key = {
        "userId": "user123"  # Replace with your key attributes
    }
    
    # Get the item
    result = await get_dynamodb_item(table_name, key)
    print(result)

def test_get_item():
    """Test retrieving an item from DynamoDB."""
    try:
        # Get the table
        table = dynamodb.Table('your-table-name')
        
        # Get the item
        response = table.get_item(Key={'id': 'test123'})
        
        # Check if item exists
        if 'Item' not in response:
            print(f"No item found with key: {{'id': 'test123'}}")
            return
            
        # Convert Decimal values to float and print the item
        item = convert_decimals(response['Item'])
        print("\nRetrieved item:")
        print(json.dumps(item, indent=2))
        
    except ClientError as e:
        print(f"Error: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if not dynamodb:
        print("AWS credentials not found or invalid. Please ensure you have valid credentials in ~/.aws/credentials:")
        print("\n1. Create or edit ~/.aws/credentials:")
        print("   [default]")
        print("   aws_access_key_id = your_access_key")
        print("   aws_secret_access_key = your_secret_key")
        print("\n2. Create or edit ~/.aws/config:")
        print("   [default]")
        print("   region = your-region  # e.g., us-east-1")
        exit(1)
    
    # Run the async main function
    asyncio.run(main()) 