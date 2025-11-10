from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load data from JSON file
def load_data():
    # IMPORTANT: This assumes 'data.json' is in the same directory as app.py
    # Make sure you've included data.json in your GitHub repo.
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "data.json file not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}

@app.route('/')
def home():
    return jsonify({
        "message": "Car Makes and Models API",
        "version": "2.0",
        "endpoints": {
            "/api/brands": "Get all car brands and models with years",
            "/api/brands/<brand_name>": "Get models for a specific brand",
            "/api/brands/search?model=<name>&year=<year>": "Search for models by name or year",
            "/api/count": "Get statistics about brands and models"
        }
    })

@app.route('/api/brands', methods=['GET'])
def get_all_brands():
    """Get all car brands and their models"""
    data = load_data()
    return jsonify(data)

@app.route('/api/brands/<string:brand_name>', methods=['GET'])
def get_brand_models(brand_name):
    """Get models for a specific brand"""
    data = load_data()
    
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
    data = load_data()
    
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
    data = load_data()
    
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
    #
    # --- THIS IS THE FIX FOR PROBLEM #2 ---
    # Appwrite requires your server to listen on port 3000
    #
    port = 3000
    app.run(host='0.0.0.0', port=port, debug=False)