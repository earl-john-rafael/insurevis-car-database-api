from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import sys # Import sys to print errors

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

#
# --- THIS IS THE NEW, EFFICIENT WAY ---
# Load the data ONCE when the server starts.
#
def load_data_globally():
    """Loads data from data.json into a global variable."""
    try:
        # Assumes 'data.json' is in the root, next to this app.py
        with open('data.json', 'r', encoding='utf-8') as f:
            print("Successfully opened data.json")
            data = json.load(f)
            print(f"Successfully loaded data.json. Found {len(data.get('brands', []))} brands.")
            return data
    except FileNotFoundError:
        print("!!! ERROR: data.json file not found !!!", file=sys.stderr)
        return {"error": "data.json file not found"}
    except json.JSONDecodeError:
        print("!!! ERROR: Invalid JSON format in data.json !!!", file=sys.stderr)
        return {"error": "Invalid JSON format"}
    except Exception as e:
        print(f"!!! AN UNKNOWN ERROR OCCURRED: {e} !!!", file=sys.stderr)
        return {"error": f"An unknown error occurred: {e}"}

# Load the data into a global variable called APP_DATA
APP_DATA = load_data_globally()

@app.route('/health')
def health_check():
    """A simple health check endpoint that doesn't use the data."""
    return jsonify({"status": "ok"})

@app.route('/')
def home():
    return jsonify({
        "message": "Car Makes and Models API",
        "version": "2.0",
        "endpoints": {
            "/api/brands": "Get all car brands and models with years",
            "/api/brands/<brand_name>": "Get models for a specific brand",
            "/api/brands/search?model=<name>&year=<year>": "Search for models by name or year",
            "/api/count": "Get statistics about brands and models",
            "/health": "Simple health check"
        }
    })

@app.route('/api/brands', methods=['GET'])
def get_all_brands():
    """Get all car brands and their models"""
    # Use the pre-loaded data
    return jsonify(APP_DATA)

@app.route('/api/brands/<string:brand_name>', methods=['GET'])
def get_brand_models(brand_name):
    """Get models for a specific brand"""
    # Use the pre-loaded data
    data = APP_DATA
    
    if "error" in data:
        return jsonify(data), 500
    
    # Search for the brand (case-insensitive)
    for brand in data.get('brands', []):
        if brand['name'].lower() == brand_name.lower():
            return jsonify(brand)
    
    return jsonify({"error": f"Brand '{brand_name}' not found"}), 404

@app.route('/api/brands/search', methods=['GET'])
def search_models():
    """Search for models by name or year"""
    # Use the pre-loaded data
    data = APP_DATA
    
    if "error" in data:
        return jsonify(data), 500
    
    model_name = request.args.get('model', '').lower()
    year = request.args.get('year', '')
    
    results = []
    
    for brand in data.get('brands', []):
        for model in brand.get('models', []):
            match = True
            
            if model_name and model_name not in model.get('model_name', '').lower():
                match = False
            
            if year and str(model.get('year', '')) != year:
                match = False
            
            if match:
                results.append({
                    'brand': brand['name'],
                    'model_name': model.get('model_name'),
                    'year': model.get('year')
                })
    
    return jsonify({
        "count": len(results),
        "results": results
    })

@app.route('/api/count', methods=['GET'])
def get_statistics():
    """Get statistics about the data"""
    # Use the pre-loaded data
    data = APP_DATA
    
    if "error" in data:
        return jsonify(data), 500
    
    brands = data.get('brands', [])
    total_brands = len(brands)
    total_models = sum(len(brand.get('models', [])) for brand in brands)
    
    # Get year range
    all_years = []
    for brand in brands:
        for model in brand.get('models', []):
            year = model.get('year')
            if year:
                all_years.append(year)
    
    return jsonify({
        "total_brands": total_brands,
        "total_models": total_models,
        "year_range": {
            "min": min(all_years) if all_years else None,
            # --- BUG FIX ---
            # This was 'all_models', now fixed to 'all_years'
            "max": max(all_years) if all_years else None
        },
        "brands": [brand['name'] for brand in brands]
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = 3000
    app.run(host='0.0.0.0', port=port, debug=False)

#
# --- THIS IS THE MAJOR CHANGE ---
# We remove the if __name__ == '__main__' block completely.
# Gunicorn will start the server, so we don't need app.run() at all.
#