import asyncio
import httpx
import json

async def test_spoonacular_search():
    """Test the Spoonacular API search endpoint with a simple query."""
    api_key = "fcb0555d1dda4a089ec07426bdb9aeb4"
    
    # Simple test parameters
    params = {
        'query': 'pasta',
        'number': 2,  # Limit to 2 results for testing
        'addRecipeInformation': True
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.spoonacular.com/recipes/complexSearch',
                params=params,
                headers={'x-api-key': api_key},
                timeout=30.0
            )
            
            if response.status_code == 200:
                results = response.json()
                print("\nSearch Results:")
                print(json.dumps(results, indent=2))
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_spoonacular_search()) 