import json
import os
import uuid
import httpx
import asyncio
from typing import List, Dict, Any

# Constants
INSTACART_API_BASE = "https://connect.dev.instacart.tools/idp/v1"

async def place_grocery_order(items: List[Dict[str, Any]]) -> str:
    """Place a grocery delivery order on Instacart.
    
    Args:
        items: List of grocery items, where each item is a dict with:
            - name: Name of the item
            - quantity: Quantity of the item
            - unit: Unit of measurement (e.g. 'each', 'lb', 'oz')
    """
    try:
        # Get Instacart API credentials
        instacart_credentials = json.loads(os.environ.get('INSTACART_API_CREDENTIALS', '{}'))
        if not instacart_credentials:
            return "Error: Instacart API credentials not found. Please set INSTACART_API_CREDENTIALS environment variable."
        
        # Initialize Instacart API client
        headers = {
            'Authorization': f"Bearer {instacart_credentials['api_key']}",
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
            print(recipe_response)
            return f"Order placed successfully! Order ID: {recipe_response.get('products_link_url', 'Unknown')}"
            
    except Exception as e:
        return f"Error placing order: {str(e)}"

async def main():
    # Example grocery items
    items = [
        {"name": "Milk", "quantity": 1, "unit": "gallon"},
        {"name": "Eggs", "quantity": 12, "unit": "each"},
        {"name": "Bread", "quantity": 1, "unit": "loaf"},
        {"name": "Apples", "quantity": 5, "unit": "each"},
        {"name": "Chicken Breast", "quantity": 2, "unit": "lb"}
    ]
    
    # Place the order
    result = await place_grocery_order(items)
    print(result)

if __name__ == "__main__":
    # Check if API credentials are set
    if not os.environ.get('INSTACART_API_CREDENTIALS'):
        print("Please set the INSTACART_API_CREDENTIALS environment variable first.")
        print("Example:")
        print('export INSTACART_API_CREDENTIALS=\'{"api_key": "your_api_key"}\'')
        exit(1)
        
    # Run the async main function
    asyncio.run(main()) 