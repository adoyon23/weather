from typing import Any
import httpx
import json
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
import logging
from decimal import Decimal

# Initialize FastMCP server
PORT = 8000
mcp = FastMCP("weather", port=PORT)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
INSTACART_API_BASE = "https://connect.dev.instacart.tools/idp/v1"

def convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    return obj

# Initialize DynamoDB client using credentials from ~/.aws/credentials
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

@mcp.tool()
async def get_dynamodb_item(table_name: str, key: dict) -> str:
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

@mcp.tool()
async def place_grocery_order(items: list[dict]) -> str:
    """Place a grocery delivery order on Instacart.
    
    Args:
        items: List of grocery items, where each item is a dict with:
            - name: Name of the item
            - quantity: Quantity of the item
            - unit: Unit of measurement (e.g. 'each', 'lb', 'oz')
    """
    try:
        # Get Instacart API credentials
        instacart_credentials = os.environ.get('INSTACART_API_CREDENTIALS')
        if not instacart_credentials:
            return "Error: Instacart API credentials not found. Please set INSTACART_API_CREDENTIALS environment variable."
        
        # Initialize Instacart API client
        headers = {
            'Authorization': f"Bearer {instacart_credentials}",
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Create recipe data
        recipe_data = {
            'title': 'Grocery Order',
            'author': 'AI Assistant',
            'servings': 1,
            'cooking_time': 30,  # Default 30 minutes
            'external_reference_id': str(uuid.uuid4()),
            'expires_in': 30,  # Link expires in 30 days
            'ingredients': [
                {
                    'name': item['name'],
                    'display_text': f"{item['quantity']} {item['name']}",
                    'measurements': [
                        {
                            'quantity': item['quantity'],
                            'unit': item.get('unit', 'each')  # Default to 'each' if unit not specified
                        }
                    ]
                }
                for item in items
            ],
            'landing_page_configuration': {
                'partner_linkback_url': 'https://your-website.com',  # Replace with your website URL
                'enable_pantry_items': True
            }
        }
        
        # Make API call to create recipe page
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{INSTACART_API_BASE}/products/recipe',
                headers=headers,
                json=recipe_data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                return f"Error placing order: {response.text}"
            
            recipe_response = response.json()
            return f"Order placed successfully! Order ID: {recipe_response.get('products_link_url', 'Unknown')}"
            
    except Exception as e:
        logger.error(f"Error placing grocery order: {str(e)}")
        return f"Error placing order: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    logger.info(f"Starting weather server on port {PORT}")
    logger.info(f"Liggubg ssdft")
    mcp.run(transport='stdio')
