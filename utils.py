import json
import pandas as pd
from typing import List, Dict, Any
import os

def load_university_data() -> List[Dict[str, Any]]:
    """Load university data from JSON file."""
    try:
        with open('data/universities.json', 'r') as f:
            data = json.load(f)
            return data['universities']
    except FileNotFoundError:
        return []

def filter_universities(
    universities: List[Dict[str, Any]],
    budget: float,
    gpa: float,
    preferred_country: str,
    degree: str
) -> List[Dict[str, Any]]:
    """Filter universities based on user criteria."""
    filtered = []
    
    for uni in universities:
        # Check if university is in preferred country
        if preferred_country not in uni['city_country']:
            continue
            
        # Check if degree matches (case-insensitive partial match)
        if degree.lower() not in uni['program_title'].lower():
            continue
            
        # Check if tuition is within budget
        if uni['tuition_fees'] > budget:
            continue
            
        # Check if GPA requirement is met
        min_gpa = float(uni['requirements']['GPA'])
        if gpa < min_gpa:
            continue
            
        filtered.append(uni)
    
    return filtered

def generate_excel(universities: List[Dict[str, Any]]) -> str:
    """Generate Excel file from university data."""
    if not universities:
        return None
        
    # Flatten the data for Excel
    flattened_data = []
    for uni in universities:
        row = {
            'University Name': uni['university_name'],
            'Location': uni['city_country'],
            'Program': uni['program_title'],
            'Tuition Fees': uni['tuition_fees'],
            'Program Page': uni['program_page'],
            'Application Link': uni['application_link'],
            'IELTS Requirement': uni['requirements']['IELTS'],
            'TOEFL Requirement': uni['requirements']['TOEFL'],
            'GRE Requirement': uni['requirements']['GRE'],
            'GPA Requirement': uni['requirements']['GPA'],
            'Scholarships': ', '.join(s['name'] for s in uni['scholarships'])
        }
        flattened_data.append(row)
    
    df = pd.DataFrame(flattened_data)
    
    # Create exports directory if it doesn't exist
    os.makedirs('exports', exist_ok=True)
    
    # Save to Excel
    filename = 'exports/universities.xlsx'
    df.to_excel(filename, index=False)
    return filename 