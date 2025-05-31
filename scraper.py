import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API with the provided key
GOOGLE_API_KEY = "AIzaSyAIhDwrBi9hf0Nn4L1-jHyLpJGv-oSIS2M"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def is_valid_url(url: str) -> bool:
    """Check if URL is valid and accessible."""
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    except:
        return False

def scrape_webpage(url: str) -> str:
    """Scrape webpage content from given URL with improved error handling."""
    if not is_valid_url(url):
        print(f"Invalid URL: {url}")
        return ""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Add delay to be respectful to servers
        time.sleep(1)
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # Check if content is HTML
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            print(f"Non-HTML content for {url}: {content_type}")
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
            element.decompose()
        
        # Focus on main content areas
        main_content = soup.find('main') or soup.find('div', class_=re.compile(r'content|main', re.I)) or soup.find('body')
        
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line and len(line) > 3:  # Filter out very short lines
                lines.append(line)
        
        cleaned_text = '\n'.join(lines)
        
        # Limit text length to avoid token limits
        if len(cleaned_text) > 8000:
            cleaned_text = cleaned_text[:8000] + "..."
        
        return cleaned_text
        
    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {str(e)}")
        return ""
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return ""

def extract_university_info(webpage_content: str, url: str) -> Dict[str, Any]:
    """Use Gemini to extract structured information from webpage content."""
    if not webpage_content or len(webpage_content.strip()) < 100:
        return {}
    
    prompt = f"""
    Analyze this university program webpage content and extract the following information:
    
    1. Program title/name
    2. Tuition fees (convert to USD if necessary, provide annual amount)
    3. Academic requirements (GPA, minimum scores)
    4. English language requirements (IELTS, TOEFL scores)
    5. Standardized test requirements (GRE, GMAT)
    6. Application deadlines
    7. Program duration
    8. Any additional requirements or notes
    
    Webpage content:
    {webpage_content}
    
    Respond with a valid JSON object using these exact keys:
    {{
        "program_title": "string or null",
        "tuition_fees": number or null,
        "requirements": {{
            "GPA": "string or null",
            "IELTS": "string or null", 
            "TOEFL": "string or null",
            "GRE": "string or null",
            "GMAT": "string or null"
        }},
        "application_deadline": "string or null",
        "program_duration": "string or null",
        "additional_notes": "string or null"
    }}
    
    Guidelines:
    - For tuition_fees, extract only the number (e.g., 25000 for $25,000)
    - For requirements, include minimum scores (e.g., "6.5" for IELTS, "3.0" for GPA)
    - Use null if information is not clearly stated
    - Be precise and conservative in extraction
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean response text
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*$', '', response_text)
        response_text = response_text.strip()
        
        info = json.loads(response_text)
        info['source_url'] = url
        info['scraped'] = True
        
        return info
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error for {url}: {str(e)}")
        print(f"Response text: {response.text[:500]}...")
        return {}
    except Exception as e:
        print(f"Error extracting info with Gemini for {url}: {str(e)}")
        return {}

def validate_university_data(uni_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean university data."""
    required_fields = ['university_name', 'program_title', 'city_country']
    
    # Check if essential fields are present
    for field in required_fields:
        if not uni_data.get(field):
            return {}
    
    # Ensure requirements is a dict
    if 'requirements' not in uni_data or not isinstance(uni_data['requirements'], dict):
        uni_data['requirements'] = {
            "GPA": None,
            "IELTS": None,
            "TOEFL": None,
            "GRE": None,
            "GMAT": None
        }
    
    # Validate tuition fees
    if 'tuition_fees' in uni_data:
        try:
            if uni_data['tuition_fees']:
                uni_data['tuition_fees'] = float(uni_data['tuition_fees'])
        except (ValueError, TypeError):
            uni_data['tuition_fees'] = None
    
    return uni_data

def search_universities_with_gemini(
    budget: float,
    gpa: float,
    preferred_country: str,
    degree: str
) -> List[Dict[str, Any]]:
    """Search for universities using Gemini AI with improved accuracy."""
    
    prompt = f"""
    Find 5 real, accredited universities that match these specific criteria:
    
    Criteria:
    - Maximum tuition budget: ${budget:,.0f} USD per year
    - Student GPA: {gpa}/4.0
    - Country: {preferred_country}
    - Degree program: {degree}
    
    Requirements:
    1. Universities must be real and accredited
    2. Tuition fees must be at or below ${budget:,.0f} USD annually
    3. GPA requirements should be at or below {gpa}/4.0
    4. Programs must be available for international students
    5. Provide actual, working URLs to program pages
    
    For each university, provide this exact JSON structure:
    {{
        "university_name": "Full official university name",
        "city_country": "City, {preferred_country}",
        "program_title": "Specific program name for {degree}",
        "program_page": "https://actual-university-website.edu/program-page",
        "application_link": "https://actual-university-website.edu/apply",
        "tuition_fees": annual_tuition_in_USD_number,
        "requirements": {{
            "GPA": "minimum GPA as string",
            "IELTS": "minimum IELTS score as string or null",
            "TOEFL": "minimum TOEFL score as string or null", 
            "GRE": "GRE requirement as string or null",
            "GMAT": "GMAT requirement as string or null"
        }},
        "program_duration": "duration (e.g., '2 years', '18 months')",
        "application_deadline": "deadline information"
    }}
    
    Return only a valid JSON array of exactly 5 universities. Do not include any markdown formatting or explanatory text.
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean the response
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*$', '', response_text)
        response_text = response_text.strip()
        
        universities = json.loads(response_text)
        
        if not isinstance(universities, list):
            print("Response is not a list")
            return []
        
        enhanced_universities = []
        
        for i, uni in enumerate(universities):
            print(f"Processing university {i+1}: {uni.get('university_name', 'Unknown')}")
            
            # Validate basic structure
            validated_uni = validate_university_data(uni)
            if not validated_uni:
                print(f"Skipping invalid university data: {uni.get('university_name', 'Unknown')}")
                continue
            
            # Try to scrape additional information
            program_url = validated_uni.get('program_page')
            if program_url and is_valid_url(program_url):
                print(f"Scraping: {program_url}")
                webpage_content = scrape_webpage(program_url)
                
                if webpage_content:
                    additional_info = extract_university_info(webpage_content, program_url)
                    
                    # Merge scraped data with original data (original takes precedence for key fields)
                    for key, value in additional_info.items():
                        if key not in ['university_name', 'city_country'] and value:
                            if key == 'requirements':
                                # Merge requirements carefully
                                if isinstance(value, dict):
                                    for req_key, req_value in value.items():
                                        if req_value and not validated_uni['requirements'].get(req_key):
                                            validated_uni['requirements'][req_key] = req_value
                            elif not validated_uni.get(key):
                                validated_uni[key] = value
                    
                    print(f"Successfully scraped and enhanced data for {validated_uni['university_name']}")
                else:
                    print(f"Failed to scrape content from {program_url}")
            else:
                print(f"Invalid or missing program URL: {program_url}")
            
            enhanced_universities.append(validated_uni)
        
        print(f"Successfully processed {len(enhanced_universities)} universities")
        return enhanced_universities
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error in search: {str(e)}")
        print(f"Response text preview: {response.text[:500]}...")
        return []
    except Exception as e:
        print(f"Error searching universities with Gemini: {str(e)}")
        return []

def get_fallback_universities(preferred_country: str, degree: str, budget: float, gpa: float) -> List[Dict[str, Any]]:
    """Provide fallback university data if scraping fails."""
    fallback_data = {
        "USA": [
            {
                "university_name": "Arizona State University",
                "city_country": "Phoenix, USA",
                "program_title": f"Master's in {degree}",
                "tuition_fees": 30000,
                "requirements": {"GPA": "3.0", "IELTS": "6.5", "TOEFL": "80"},
                "program_duration": "2 years",
                "application_deadline": "Rolling admissions"
            }
        ],
        "Canada": [
            {
                "university_name": "University of Regina",
                "city_country": "Regina, Canada", 
                "program_title": f"Master's in {degree}",
                "tuition_fees": 25000,
                "requirements": {"GPA": "3.0", "IELTS": "6.5", "TOEFL": "80"},
                "program_duration": "2 years",
                "application_deadline": "Multiple intakes"
            }
        ],
        "UK": [
            {
                "university_name": "University of Greenwich",
                "city_country": "London, UK",
                "program_title": f"Master's in {degree}",
                "tuition_fees": 18000,
                "requirements": {"GPA": "3.0", "IELTS": "6.0", "TOEFL": "75"},
                "program_duration": "1 year",
                "application_deadline": "Rolling admissions"
            }
        ],
        "Germany": [
            {
                "university_name": "University of Applied Sciences",
                "city_country": "Berlin, Germany",
                "program_title": f"Master's in {degree}",
                "tuition_fees": 3000,
                "requirements": {"GPA": "2.8", "IELTS": "6.0", "TOEFL": "80"},
                "program_duration": "2 years",
                "application_deadline": "Winter/Summer semesters"
            }
        ],
        "Australia": [
            {
                "university_name": "Griffith University",
                "city_country": "Brisbane, Australia",
                "program_title": f"Master's in {degree}",
                "tuition_fees": 32000,
                "requirements": {"GPA": "3.0", "IELTS": "6.5", "TOEFL": "79"},
                "program_duration": "2 years",
                "application_deadline": "Multiple intakes"
            }
        ]
    }
    
    return fallback_data.get(preferred_country, [])