from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from jsonschema import validate, ValidationError
import os
import pandas as pd
from utils import load_university_data, filter_universities, generate_excel
from scraper import search_universities_with_gemini

app = Flask(__name__)
CORS(app)

# Input validation schema
search_schema = {
    "type": "object",
    "properties": {
        "budget": {"type": "number", "minimum": 0},
        "gpa": {"type": "number", "minimum": 0, "maximum": 4.0},
        "linkedin": {"type": "string"},
        "preferred_country": {"type": "string", "enum": ["USA", "Canada", "UK", "Germany", "Australia"]},
        "degree": {"type": "string", "minLength": 1}
    },
    "required": ["budget", "gpa", "preferred_country", "degree"]
}

# Global variable to store last search results
last_results = []

@app.route('/api/search_universities', methods=['POST'])
def search_universities():
    """
    Search for universities based on user criteria and scrape additional data.
    """
    try:
        data = request.get_json()
        
        # Validate input
        validate(instance=data, schema=search_schema)
        
        # Load static university data
        static_universities = load_university_data()
        
        # Get dynamic data from Gemini and web scraping
        scraped_universities = search_universities_with_gemini(
            budget=data['budget'],
            gpa=data['gpa'],
            preferred_country=data['preferred_country'],
            degree=data['degree']
        )
        
        # Combine and filter universities
        all_universities = static_universities + scraped_universities
        filtered_unis = filter_universities(
            universities=all_universities,
            budget=data['budget'],
            gpa=data['gpa'],
            preferred_country=data['preferred_country'],
            degree=data['degree']
        )
        
        # Store results for Excel download
        global last_results
        last_results = filtered_unis
        
        return jsonify(filtered_unis)
        
    except ValidationError as e:
        return jsonify({
            "error": "Invalid input",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.route("/api/check_health", methods=["GET"])
def check_health():
    """
    Check the health of the API.
    """
    return jsonify({"status": "healthy"}), 200

@app.route('/api/download_excel', methods=['GET'])
def download_excel():
    """
    Download the last search results as Excel file.
    """
    try:
        global last_results
        if not last_results:
            return jsonify({
                "error": "No data available"
            }), 404
            
        # Generate Excel file
        excel_file = generate_excel(last_results)
        
        if not excel_file:
            return jsonify({
                "error": "No data available"
            }), 404
            
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='universities.xlsx'
        )
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000) 