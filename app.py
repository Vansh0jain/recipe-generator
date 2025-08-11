from flask import Flask, request, jsonify, render_template
import requests
import uuid
import os
from datetime import datetime

app = Flask(__name__)

# Load API key from environment variable
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"

def generate_recipe(ingredients, dietary_restrictions=None, cuisine=None, meal_type=None):
    """Generate a recipe based on ingredients and optional parameters"""
    headers = {
        "Content-Type": "application/json"
    }

    # Build additional context based on optional parameters
    additional_context = ""
    if dietary_restrictions:
        additional_context += f"This recipe must be suitable for {dietary_restrictions} diet. "
    if cuisine:
        additional_context += f"Create a {cuisine} style dish. "
    if meal_type:
        additional_context += f"This should be a {meal_type}. "

    prompt = f"""
    You are RecipeGenius, an expert chef specialized in creating recipes from available ingredients. 
    Given the following ingredients: {ingredients}, create a delicious and creative recipe.
    {additional_context}

    Your response must follow this exact format:

    # [Creative Recipe Name]

    ## Ingredients
    - Complete list of ingredients with precise measurements
    - Include the provided ingredients: {ingredients}
    - Add any basic ingredients that might be needed (salt, pepper, oil, etc.)

    ## Preparation Time
    - Total preparation time
    - Cooking time

    ## Difficulty Level
    - Easy/Medium/Hard

    ## Instructions
    1. Clear step-by-step instructions
    2. Include cooking temperatures and times
    3. Describe techniques in detail

    ## Serving Suggestions
    - How to plate and serve
    - Recommended sides or garnishes

    ## Chef's Notes
    - One unique tip or variation
    - Substitution suggestions for common allergens or dietary restrictions

    Remember to be creative, use interesting flavor combinations, and ensure the recipe is practical and executable with common kitchen equipment.
    """

    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=body)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Request failed: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_recipe', methods=['POST'])
def generate_recipe_endpoint():
    data = request.get_json()
    
    # Get parameters with defaults
    ingredients = data.get('ingredients', '')
    dietary_restrictions = data.get('dietary_restrictions', None)
    cuisine = data.get('cuisine', None)
    meal_type = data.get('meal_type', None)
    
    if not ingredients:
        return jsonify({'error': 'Please provide ingredients'}), 400
    
    # Track request for analytics
    request_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Generate the recipe
    recipe = generate_recipe(
        ingredients, 
        dietary_restrictions, 
        cuisine, 
        meal_type
    )
    
    return jsonify({
        'id': request_id,
        'timestamp': timestamp,
        'message': recipe,
        'sender': 'bot'
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint for monitoring the health of the application"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
