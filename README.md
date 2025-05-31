# Study Abroad Assistant API

A Flask-based REST API that helps students find universities abroad based on their preferences and qualifications.

## Features

- Search universities based on budget, GPA, preferred country, and desired degree
- Download search results as Excel file
- CORS enabled for frontend integration
- Input validation
- Error handling

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The server will start at `http://localhost:5000`

## API Endpoints

### POST /api/search_universities

Search for universities based on user criteria.

**Request Body:**
```json
{
  "budget": 50000,
  "gpa": 3.5,
  "linkedin": "https://linkedin.com/in/username",
  "preferred_country": "USA",
  "degree": "MS in Computer Science"
}
```

**Response:**
```json
[
  {
    "university_name": "Example University",
    "city_country": "City, Country",
    "program_title": "Program Name",
    "program_page": "URL",
    "application_link": "URL",
    "tuition_fees": 45000,
    "scholarships": [
      {
        "name": "Scholarship Name",
        "link": "URL"
      }
    ],
    "requirements": {
      "IELTS": "6.5",
      "TOEFL": "90",
      "GRE": "310",
      "GPA": "3.0"
    }
  }
]
```

### GET /api/download_excel

Download the university data as an Excel file.

**Response:** Excel file download

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- 400: Bad Request (Invalid input)
- 404: Not Found
- 500: Internal Server Error

## Project Structure

```
.
├── README.md
├── requirements.txt
├── app.py
├── utils.py
├── data/
│   └── universities.json
└── exports/
    └── universities.xlsx
```

## Development

- The sample university data is stored in `data/universities.json`
- Excel files are generated in the `exports` directory
- Add more universities by updating the JSON file
- Modify filtering logic in `utils.py`

## Future Improvements

- Add user authentication
- Implement caching for search results
- Add more sophisticated university matching algorithms
- Integrate with real university databases
- Add more filtering options 