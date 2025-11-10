import json
import os
import sys

# We don't need 'appwrite' SDK for this,
# but we'll leave it in requirements.txt
# in case you want it later.

def load_data():
    """Loads data from data.json."""
    # Appwrite runs the script from the root,
    # so the path should be correct.
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "data.json file not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}
    except Exception as e:
        return {"error": f"An unknown error occurred: {e}"}

def main(context):
    """
    This is the new entrypoint.
    It handles one request and then exits.
    """
    
    # Load the car data on every execution
    data = load_data()

    # If data loading failed, return an error immediately
    if "error" in data:
        return context.res.json(data, 500)

    #
    # --- This is our new "Router" ---
    #
    
    path = context.req.path
    
    # 1. Handle '/' (Home)
    if path == '/':
        return context.res.json({
            "message": "Car Makes and Models API",
            "version": "2.0",
            "endpoints": {
                "/api/brands": "Get all car brands and models with years",
                "/api/brands/<brand_name>": "Get models for a specific brand",
                "/api/brands/search?model=<name>&year=<year>": "Search for models by name or year",
                "/api/count": "Get statistics about brands and models"
            }
        })

    # 2. Handle '/api/brands' (Get All)
    if path == '/api/brands':
        return context.res.json(data)

    # 3. Handle '/api/brands/search' (Search)
    if path == '/api/brands/search':
        model_name = context.req.query.get('model', '').lower()
        year = context.req.query.get('year', '')
        
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
        
        return context.res.json({
            "count": len(results),
            "results": results
        })

    # 4. Handle '/api/count' (Statistics)
    if path == '/api/count':
        brands = data.get('brands', [])
        total_brands = len(brands)
        total_models = sum(len(brand.get('models', [])) for brand in brands)
        
        all_years = []
        for brand in brands:
            for model in brand.get('models', []):
                year = model.get('year')
                if year:
                    all_years.append(year)
        
        return context.res.json({
            "total_brands": total_brands,
            "total_models": total_models,
            "year_range": {
                "min": min(all_years) if all_years else None,
                "max": max(all_years) if all_years else None
            },
            "brands": [brand['name'] for brand in brands]
        })

    # 5. Handle '/api/brands/<brand_name>' (Get Specific Brand)
    #    This must be *after* '/api/brands/search'
    if path.startswith('/api/brands/'):
        # Get brand_name from path, e.g., /api/brands/Toyota
        brand_name = path.split('/')[-1]
        
        for brand in data.get('brands', []):
            if brand['name'].lower() == brand_name.lower():
                return context.res.json(brand)
        
        return context.res.json({"error": f"Brand '{brand_name}' not found"}, 404)

    # Default 404
    return context.res.json({"error": "Endpoint not found"}, 404)