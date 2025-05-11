from typing import Any, Optional, List, Union
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
from typing import TypedDict, NotRequired
import http.server
import socketserver
import threading
import webbrowser
from jinja2 import Template

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

class RecipeSearchParams(TypedDict, total=False):
    query: NotRequired[str]
    cuisine: NotRequired[str]
    excludeCuisine: NotRequired[str]
    diet: NotRequired[str]
    intolerances: NotRequired[str]
    equipment: NotRequired[str]
    includeIngredients: NotRequired[str]
    excludeIngredients: NotRequired[str]
    type: NotRequired[str]
    instructionsRequired: NotRequired[bool]
    fillIngredients: NotRequired[bool]
    addRecipeInformation: NotRequired[bool]
    addRecipeInstructions: NotRequired[bool]
    addRecipeNutrition: NotRequired[bool]
    author: NotRequired[str]
    tags: NotRequired[str]
    recipeBoxId: NotRequired[int]
    titleMatch: NotRequired[str]
    maxReadyTime: NotRequired[int]
    minServings: NotRequired[int]
    maxServings: NotRequired[int]
    ignorePantry: NotRequired[bool]
    sort: NotRequired[str]
    sortDirection: NotRequired[str]
    minCarbs: NotRequired[float]
    maxCarbs: NotRequired[float]
    minProtein: NotRequired[float]
    maxProtein: NotRequired[float]
    minCalories: NotRequired[float]
    maxCalories: NotRequired[float]
    minFat: NotRequired[float]
    maxFat: NotRequired[float]
    minAlcohol: NotRequired[float]
    maxAlcohol: NotRequired[float]
    minCaffeine: NotRequired[float]
    maxCaffeine: NotRequired[float]
    minCopper: NotRequired[float]
    maxCopper: NotRequired[float]
    minCalcium: NotRequired[float]
    maxCalcium: NotRequired[float]
    minCholine: NotRequired[float]
    maxCholine: NotRequired[float]
    minCholesterol: NotRequired[float]
    maxCholesterol: NotRequired[float]
    minFluoride: NotRequired[float]
    maxFluoride: NotRequired[float]
    minSaturatedFat: NotRequired[float]
    maxSaturatedFat: NotRequired[float]
    minVitaminA: NotRequired[float]
    maxVitaminA: NotRequired[float]
    minVitaminC: NotRequired[float]
    maxVitaminC: NotRequired[float]
    minVitaminD: NotRequired[float]
    maxVitaminD: NotRequired[float]
    minVitaminE: NotRequired[float]
    maxVitaminE: NotRequired[float]
    minVitaminK: NotRequired[float]
    maxVitaminK: NotRequired[float]
    minVitaminB1: NotRequired[float]
    maxVitaminB1: NotRequired[float]
    minVitaminB2: NotRequired[float]
    maxVitaminB2: NotRequired[float]
    minVitaminB5: NotRequired[float]
    maxVitaminB5: NotRequired[float]
    minVitaminB3: NotRequired[float]
    maxVitaminB3: NotRequired[float]
    minVitaminB6: NotRequired[float]
    maxVitaminB6: NotRequired[float]
    minVitaminB12: NotRequired[float]
    maxVitaminB12: NotRequired[float]
    minFiber: NotRequired[float]
    maxFiber: NotRequired[float]
    minFolate: NotRequired[float]
    maxFolate: NotRequired[float]
    minFolicAcid: NotRequired[float]
    maxFolicAcid: NotRequired[float]
    minIodine: NotRequired[float]
    maxIodine: NotRequired[float]
    minIron: NotRequired[float]
    maxIron: NotRequired[float]
    minMagnesium: NotRequired[float]
    maxMagnesium: NotRequired[float]
    minManganese: NotRequired[float]
    maxManganese: NotRequired[float]
    minPhosphorus: NotRequired[float]
    maxPhosphorus: NotRequired[float]
    minPotassium: NotRequired[float]
    maxPotassium: NotRequired[float]
    minSelenium: NotRequired[float]
    maxSelenium: NotRequired[float]
    minSodium: NotRequired[float]
    maxSodium: NotRequired[float]
    minSugar: NotRequired[float]
    maxSugar: NotRequired[float]
    minZinc: NotRequired[float]
    maxZinc: NotRequired[float]
    offset: NotRequired[int]
    number: NotRequired[int]

@mcp.tool()
async def search_recipes(params: RecipeSearchParams) -> str:
    """Search for recipes using the Spoonacular API with advanced filtering and ranking.
    
    Args:
        params: A dictionary containing any of the following search parameters:
            - query: Natural language recipe search query
            - cuisine: Comma-separated list of cuisines
            - excludeCuisine: Comma-separated list of cuisines to exclude
            - diet: Comma-separated list of diets (use | for OR, comma for AND)
            - intolerances: Comma-separated list of intolerances
            - equipment: Comma-separated list of required equipment
            - includeIngredients: Comma-separated list of ingredients to include
            - excludeIngredients: Comma-separated list of ingredients to exclude
            - type: Type of recipe (e.g., main course, dessert)
            - instructionsRequired: Whether recipes must have instructions
            - fillIngredients: Add information about ingredients
            - addRecipeInformation: Get more information about recipes
            - addRecipeInstructions: Get analyzed instructions
            - addRecipeNutrition: Get nutritional information
            - author: Username of recipe author
            - tags: User-defined tags
            - recipeBoxId: ID of recipe box to search
            - titleMatch: Text that must be in recipe title
            - maxReadyTime: Maximum preparation time in minutes
            - minServings: Minimum number of servings
            - maxServings: Maximum number of servings
            - ignorePantry: Whether to ignore pantry items
            - sort: Sorting strategy
            - sortDirection: 'asc' or 'desc'
            - Various min/max nutrient parameters (carbs, protein, calories, etc.)
            - offset: Number of results to skip (0-900)
            - number: Number of results to return (1-100)
    """
    try:
        # Get Spoonacular API key from environment
        api_key = os.environ.get('SPOONACULAR_API_KEY')
        if not api_key:
            return "Error: Spoonacular API key not found. Please set SPOONACULAR_API_KEY environment variable."
        
        # Initialize API client
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Make API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.spoonacular.com/recipes/complexSearch',
                headers=headers,
                params={**params, 'apiKey': api_key},
                timeout=30.0
            )
            
            if response.status_code != 200:
                return f"Error searching recipes: {response.text}"
            
            # Return formatted results
            results = response.json()
            return json.dumps(results, indent=2)
            
    except Exception as e:
        logger.error(f"Error searching recipes: {str(e)}")
        return f"Error searching recipes: {str(e)}"
    
    # Define a prompt to guide the LLM through the information collection
@mcp.prompt()
def collect_user_info() -> str:
    """Prompt the LLM to collect user information in a structured way"""
    return """
    Your task is to collect the following information from the user:
    1. Age (in years)
    2. Weight (in kg)
    3. Height (in cm)

    Instructions:
    - First, ask for ALL information at once in a friendly, conversational tone
    - If any information is missing or invalid, follow up specifically for that information
    - Use a friendly, conversational tone throughout
    - After collecting all information, calculate and share their BMI
    - Begin by introducing yourself and asking for all information

    Start the conversation by saying: "Hi there! I'm here to collect some basic health information. Could you please provide your age in years, weight in kilograms, and height in centimeters? For example: 'I'm 30 years old, weigh 70 kg, and am 175 cm tall.'"
    """

# Tool to validate age input
@mcp.tool()
def validate_age(age: int) -> str:
    """Validate the user's age input"""
    if age < 0 or age > 120:
        return "That age seems outside the normal human range. Please ask the user to confirm their age or provide a valid age."

    return "Age validated."

# Tool to validate weight input
@mcp.tool()
def validate_weight(weight_kg: float) -> str:
    """Validate the user's weight input"""
    if weight_kg < 20 or weight_kg > 300:
        return "That weight seems unusual. Please ask the user to confirm their weight in kilograms or provide a valid weight."

    return "Weight validated."

# Tool to validate height and calculate BMI
@mcp.tool()
def validate_height_and_calculate_bmi(age: int, weight_kg: float, height_cm: float) -> str:
    """Validate height and calculate BMI based on collected information"""
    if height_cm < 50 or height_cm > 250:
        return "That height seems unusual. Please ask the user to confirm their height in centimeters or provide a valid height."

    # Calculate BMI
    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)

    bmi_category = ""
    if bmi < 18.5:
        bmi_category = "underweight"
    elif bmi < 25:
        bmi_category = "normal weight"
    elif bmi < 30:
        bmi_category = "overweight"
    else:
        bmi_category = "obese"

    return f"""
    All information has been collected successfully:
    - Age: {age} years
    - Weight: {weight_kg} kg
    - Height: {height_cm} cm
    - BMI: {bmi:.1f} ({bmi_category})

    Please thank the user for providing their information and share these results with them.
    """

def load_template(template_path: str = "templates/default.html") -> str:
    """Load a template from a file."""
    try:
        with open(template_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading template: {str(e)}")
        return ""

@mcp.tool()
async def serve_html_page(data: dict, template_path: str = "templates/default.html", port: int = 8001) -> str:
    """Generate and serve an HTML webpage using Jinja2 templating.
    
    Args:
        data: A dictionary containing the data to be rendered in the template
        template_path: Path to the Jinja2 template file (default: templates/default.html)
        port: The port number to serve the page on (default: 8001)
    """
    try:
        # Load and create a Jinja2 template
        template_content = load_template(template_path)
        if not template_content:
            return "Error: Could not load template file"
            
        template = Template(template_content)
        html_content = template.render(**data)
        
        # Create a temporary HTML file
        temp_file = "temp_page.html"
        with open(temp_file, "w") as f:
            f.write(html_content)
        
        # Create a custom handler that serves our HTML file
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.path = f'/{temp_file}'
                return http.server.SimpleHTTPRequestHandler.do_GET(self)
        
        # Start the server in a separate thread
        def run_server():
            with socketserver.TCPServer(("", port), CustomHandler) as httpd:
                print(f"Serving at port {port}")
                httpd.serve_forever()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Generate the localhost URL
        url = f"http://localhost:{port}"
        
        # Try to open the browser automatically
        try:
            webbrowser.open(url)
        except:
            pass
        
        return f"HTML page is being served at: {url}\nClick the link to view the page in your browser."
        
    except Exception as e:
        logger.error(f"Error serving HTML page: {str(e)}")
        return f"Error serving HTML page: {str(e)}"

class NutrientSearchParams(TypedDict, total=False):
    minCarbs: NotRequired[float]
    maxCarbs: NotRequired[float]
    minProtein: NotRequired[float]
    maxProtein: NotRequired[float]
    minCalories: NotRequired[float]
    maxCalories: NotRequired[float]
    minFat: NotRequired[float]
    maxFat: NotRequired[float]
    minAlcohol: NotRequired[float]
    maxAlcohol: NotRequired[float]
    minCaffeine: NotRequired[float]
    maxCaffeine: NotRequired[float]
    minCopper: NotRequired[float]
    maxCopper: NotRequired[float]
    minCalcium: NotRequired[float]
    maxCalcium: NotRequired[float]
    minCholine: NotRequired[float]
    maxCholine: NotRequired[float]
    minCholesterol: NotRequired[float]
    maxCholesterol: NotRequired[float]
    minFluoride: NotRequired[float]
    maxFluoride: NotRequired[float]
    minSaturatedFat: NotRequired[float]
    maxSaturatedFat: NotRequired[float]
    minVitaminA: NotRequired[float]
    maxVitaminA: NotRequired[float]
    minVitaminC: NotRequired[float]
    maxVitaminC: NotRequired[float]
    minVitaminD: NotRequired[float]
    maxVitaminD: NotRequired[float]
    minVitaminE: NotRequired[float]
    maxVitaminE: NotRequired[float]
    minVitaminK: NotRequired[float]
    maxVitaminK: NotRequired[float]
    minVitaminB1: NotRequired[float]
    maxVitaminB1: NotRequired[float]
    minVitaminB2: NotRequired[float]
    maxVitaminB2: NotRequired[float]
    minVitaminB5: NotRequired[float]
    maxVitaminB5: NotRequired[float]
    minVitaminB3: NotRequired[float]
    maxVitaminB3: NotRequired[float]
    minVitaminB6: NotRequired[float]
    maxVitaminB6: NotRequired[float]
    minVitaminB12: NotRequired[float]
    maxVitaminB12: NotRequired[float]
    minFiber: NotRequired[float]
    maxFiber: NotRequired[float]
    minFolate: NotRequired[float]
    maxFolate: NotRequired[float]
    minFolicAcid: NotRequired[float]
    maxFolicAcid: NotRequired[float]
    minIodine: NotRequired[float]
    minIron: NotRequired[float]
    maxIron: NotRequired[float]
    minMagnesium: NotRequired[float]
    maxMagnesium: NotRequired[float]
    minManganese: NotRequired[float]
    maxManganese: NotRequired[float]
    minPhosphorus: NotRequired[float]
    maxPhosphorus: NotRequired[float]
    minPotassium: NotRequired[float]
    maxPotassium: NotRequired[float]
    minSelenium: NotRequired[float]
    maxSelenium: NotRequired[float]
    minSodium: NotRequired[float]
    maxSodium: NotRequired[float]
    minSugar: NotRequired[float]
    maxSugar: NotRequired[float]
    minZinc: NotRequired[float]
    maxZinc: NotRequired[float]
    offset: NotRequired[int]
    number: NotRequired[int]
    random: NotRequired[bool]

@mcp.tool()
async def search_recipes_by_nutrients(params: NutrientSearchParams) -> str:
    """Search for recipes based on nutritional requirements using the Spoonacular API.
    
    Args:
        params: A dictionary containing any of the following search parameters:
            - minCarbs/maxCarbs: Carbohydrate limits in grams
            - minProtein/maxProtein: Protein limits in grams
            - minCalories/maxCalories: Calorie limits
            - minFat/maxFat: Fat limits in grams
            - Various other nutrient limits (vitamins, minerals, etc.)
            - offset: Number of results to skip (0-900)
            - number: Number of results to return (1-100)
            - random: Whether to return random results within limits
    """
    try:
        # Get Spoonacular API key from environment
        api_key = os.environ.get('SPOONACULAR_API_KEY')
        if not api_key:
            return "Error: Spoonacular API key not found. Please set SPOONACULAR_API_KEY environment variable."
        
        # Initialize API client
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Make API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.spoonacular.com/recipes/findByNutrients',
                headers=headers,
                params={**params, 'apiKey': api_key},
                timeout=30.0
            )
            
            if response.status_code != 200:
                return f"Error searching recipes: {response.text}"
            
            # Return formatted results
            results = response.json()
            return json.dumps(results, indent=2)
            
    except Exception as e:
        logger.error(f"Error searching recipes by nutrients: {str(e)}")
        return f"Error searching recipes by nutrients: {str(e)}"

class IngredientSearchParams(TypedDict, total=False):
    ingredients: str  # Comma-separated list of ingredients
    number: NotRequired[int]  # Number of results (1-100)
    ranking: NotRequired[int]  # 1 to maximize used ingredients, 2 to minimize missing ingredients
    ignorePantry: NotRequired[bool]  # Whether to ignore pantry items

@mcp.tool()
async def search_recipes_by_ingredients(params: IngredientSearchParams) -> str:
    """Search for recipes based on available ingredients using the Spoonacular API.
    
    Args:
        params: A dictionary containing:
            - ingredients: Comma-separated list of ingredients to search for
            - number: Optional number of results to return (1-100, default: 10)
            - ranking: Optional ranking strategy (1: maximize used ingredients, 2: minimize missing ingredients)
            - ignorePantry: Optional flag to ignore pantry items (default: false)
    """
    try:
        # Get Spoonacular API key from environment
        api_key = os.environ.get('SPOONACULAR_API_KEY')
        if not api_key:
            return "Error: Spoonacular API key not found. Please set SPOONACULAR_API_KEY environment variable."
        
        # Validate required parameters
        if 'ingredients' not in params:
            return "Error: 'ingredients' parameter is required"
        
        # Initialize API client
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Make API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.spoonacular.com/recipes/findByIngredients',
                headers=headers,
                params={**params, 'apiKey': api_key},
                timeout=30.0
            )
            
            if response.status_code != 200:
                return f"Error searching recipes: {response.text}"
            
            # Return formatted results
            results = response.json()
            return json.dumps(results, indent=2)
            
    except Exception as e:
        logger.error(f"Error searching recipes by ingredients: {str(e)}")
        return f"Error searching recipes by ingredients: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    logger.info(f"Starting weather server on port {PORT}")
    logger.info(f"Liggubg ssdft")
    mcp.run(transport='stdio')
