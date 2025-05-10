from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

# Create an MCP server
mcp = FastMCP("User Info Collector")

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
    - Ask for only ONE piece of information at a time
    - Wait for the user's response before asking for the next piece
    - Use a friendly, conversational tone
    - After collecting all information, calculate and share their BMI
    - Begin by introducing yourself and asking for their age

    Start the conversation by saying: "Hi there! I'm here to collect some basic health information. Could you please tell me your age in years?"
    """

# Tool to validate age input
@mcp.tool()
def validate_age(age: int) -> str:
    """Validate the user's age input"""
    if age < 0 or age > 120:
        return "That age seems outside the normal human range. Please ask the user to confirm their age or provide a valid age."

    return "Age validated. Now please ask the user for their weight in kilograms (kg)."

# Tool to validate weight input
@mcp.tool()
def validate_weight(weight_kg: float) -> str:
    """Validate the user's weight input"""
    if weight_kg < 20 or weight_kg > 300:
        return "That weight seems unusual. Please ask the user to confirm their weight in kilograms or provide a valid weight."

    return "Weight validated. Now please ask the user for their height in centimeters (cm)."

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

# Run the server
if __name__ == "__main__":
    mcp.run()