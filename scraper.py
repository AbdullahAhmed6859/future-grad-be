import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API with the provided key
GOOGLE_API_KEY = "AIzaSyAIhDwrBi9hf0Nn4L1-jHyLpJGv-oSIS2M"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def scrape_webpage(url: str) -> str:
    """Scrape webpage content from given URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)
        
        return text
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return ""

def extract_university_info(webpage_content: str, url: str) -> Dict[str, Any]:
    """Use Gemini to extract structured information from webpage content."""
    prompt = f"""
    Extract the following information from this university webpage content:
    - Program title
    - Tuition fees (in USD)
    - GPA requirements
    - IELTS requirements
    - TOEFL requirements
    - GRE requirements
    - Application deadlines
    - Program duration
    
    Webpage content:
    {webpage_content[:4000]}  # Limit content length
    
    Format the response as a JSON object with these exact keys:
    program_title, tuition_fees, requirements (nested object with GPA, IELTS, TOEFL, GRE), 
    application_deadline, program_duration
    
    If a piece of information is not found, use null.
    """
    
    try:
        response = model.generate_content(prompt)
        info = json.loads(response.text)
        info['program_page'] = url
        return info
    except Exception as e:
        print(f"Error extracting info with Gemini: {str(e)}")
        return {}

def search_universities_with_gemini(
    budget: float,
    gpa: float,
    preferred_country: str,
    degree: str
) -> List[Dict[str, Any]]:
    """Search for universities using Gemini AI."""
    prompt = f"""
    Find 5 real universities that match these criteria:
    - Maximum Budget: ${budget} per year
    - Minimum GPA: {gpa}
    - Country: {preferred_country}
    - Degree: {degree}
    
    For each university, provide:
    - university_name (string)
    - city_country (string, format: "City, Country")
    - program_title (string)
    - program_page (valid URL to the program page)
    - application_link (valid URL to the application page)
    - tuition_fees (number in USD)
    - requirements: {{
        "IELTS": string or null,
        "TOEFL": string or null,
        "GRE": string or null,
        "GPA": string
    }}
    
    Format the response as a JSON array of objects with exactly these fields.
    Ensure all URLs are real and valid.
    """
    
    try:
        response = model.generate_content(prompt)
        # Extract the response text and clean it to ensure it's valid JSON
        response_text = response.text
        # Remove any markdown code block indicators if present
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        universities = json.loads(response_text)
        
        # Enhance data with scraped information
        enhanced_universities = []
        for uni in universities:
            if 'program_page' in uni:
                webpage_content = scrape_webpage(uni['program_page'])
                if webpage_content:
                    additional_info = extract_university_info(webpage_content, uni['program_page'])
                    uni.update(additional_info)
            enhanced_universities.append(uni)
        
        return enhanced_universities
    except Exception as e:
        print(f"Error searching universities with Gemini: {str(e)}")
        return [] 