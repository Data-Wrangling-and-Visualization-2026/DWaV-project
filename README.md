# DWaV Project – WVS Data Visualization

Backend + Frontend application for interactive visualization of World Values Survey (WVS) data.

## The System Provides

- REST API for WVS data
- Interactive web interface with 3D visualization
- Docker-based deployment

## Project Structure

```
project/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   └── data/
│   │       └── wvs_data.json
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                # React + Vite frontend
│   ├── src/
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

## Features

### Backend

- FastAPI REST API
- `/health` – service status
- `/data` – filter data by country, year, and region
- `/timeseries` – time series data for a country
- JSON-based data storage

### Frontend

- React + TypeScript
- 3D visualization (Three.js, React Three Fiber)
- Filters for country and year
- Connection test with backend
- Timeseries charts

## API Endpoints

### Health Check

```
GET /health
```

**Response:**
```json
{"status": "ok"}
```

### Get Data

```
GET /data?year=2017&country=Germany&region=Europe
```

Optional query params: `year`, `country`, `region`

**Example response:**
```json
[
  {
    "country": "Germany",
    "year": 2017,
    "region": "Europe",
    "values": {
      "happiness": 7.2,
      "trust": 0.61,
      "religiosity": 0.23,
      "life_satisfaction": 7.4
    },
    "embedding": { "x": 0.1, "y": 0.2, "z": 0.3 }
  }
]
```

### Get Timeseries

```
GET /timeseries?country=Germany
```

Returns year-over-year values for the specified country.

## Running Without Docker (Development)

### Backend

```bash
cd backend
python -m venv venv

# Linux / macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API docs:** http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

**Frontend:** http://localhost:3000

## Running With Docker

Make sure Docker and Docker Compose are installed.

From the project root:

```bash
docker compose up --build
```

**Services:**

- **Backend:** http://localhost:8000
- **API docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000

To stop:

```bash
docker compose down
```

## Data

Current data: `backend/app/data/wvs_data.json`

Contains mock data for development. Will be replaced with real World Values Survey data in later stages.

## Tech Stack

| Layer    | Technologies                    |
|----------|---------------------------------|
| Backend  | FastAPI, Python, Uvicorn        |
| Frontend | React, TypeScript, Vite, Three.js, Recharts, Zustand |
| DevOps   | Docker, Docker Compose          |

## Notes

- This is an early development version.
- Data structure may change.
- Real data pipeline and AI-based processing will be added in later stages.




Here's the same content in English for your README.md:

---

## Next Steps: Data Loading and Systematization into JSON

### 1. Download Data from WVS Website

The next stage is downloading the source files from the World Values Survey website. A hybrid approach is used for this:

```python
# Example code for downloading files
import requests
import os

# Direct links to files (to be added after manual retrieval)
urls = [
    "https://www.worldvaluessurvey.org/.../WVS_Trend_1981_2022_v4.1.zip",
    # Other links will be added here
]

download_folder = 'data/raw'
os.makedirs(download_folder, exist_ok=True)

for url in urls:
    filename = url.split('/')[-1]
    print(f"Downloading: {filename}")
    response = requests.get(url, stream=True)
    with open(os.path.join(download_folder, filename), 'wb') as f:
        for chunk in response.iter_content(8192):
            f.write(chunk)
    print(f"✓ {filename} downloaded")
```

### 2. Parse the Downloaded Data

After downloading, the files need to be parsed — extracting structured data and converting it into a workable format.

```python
import pandas as pd
import zipfile

# Unzip files
with zipfile.ZipFile('data/raw/WVS_Trend_1981_2022_v4.1.zip', 'r') as zip_ref:
    zip_ref.extractall('data/raw/')

# Load data into pandas (format depends on file type)
# For Stata (.dta)
df = pd.read_stata('data/raw/WVS_Trend_1981_2022_v4.1.dta')

# For SPSS (.sav)
# df = pd.read_spss('data/raw/WVS_Trend_1981_2022_v4.1.sav')

# For CSV
# df = pd.read_csv('data/raw/WVS_Trend_1981_2022_v4.1.csv')

print(f"Rows loaded: {len(df)}")
print(f"Columns loaded: {len(df.columns)}")
```

### 3. Systematize Data into JSON Files

The next important step is transforming the parsed data into structured JSON files for convenient use in further analysis.

```python
import json
import numpy as np

def convert_to_json(df, output_file='data/processed/wvs_data.json'):
    """
    Convert DataFrame to JSON with proper structure
    """
    # Create output directory
    os.makedirs('data/processed', exist_ok=True)
    
    # Handle special data types for JSON serialization
    def handle_special_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return obj
    
    # Convert DataFrame to list of dictionaries
    records = df.to_dict(orient='records')
    
    # Process each record
    processed_records = []
    for record in records:
        processed_record = {}
        for key, value in record.items():
            processed_record[key] = handle_special_types(value)
        processed_records.append(processed_record)
    
    # Create JSON structure
    json_data = {
        "metadata": {
            "source": "World Values Survey",
            "version": "v4.1",
            "wave": "1981-2022 Trend",
            "total_respondents": len(df),
            "total_variables": len(df.columns),
            "export_date": "2024-01-15"
        },
        "variables": list(df.columns),
        "data": processed_records
    }
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"JSON file saved: {output_file}")
    print(f"File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")

# Run conversion
convert_to_json(df)
```

### 4. Create Categorized JSON Files

For analysis convenience, the data can be split into multiple thematic JSON files:

```python
def create_categorized_json(df):
    """
    Split data into categories and save as separate JSON files
    """
    
    # Example categories for WVS
    categories = {
        "demographics": ["country", "gender", "age", "education", "income"],
        "values": ["trust", "religion", "politics", "family"],
        "wellbeing": ["happiness", "life_satisfaction", "health"],
        "country_stats": ["country", "gdp", "population"]
    }
    
    def handle_special_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return obj
    
    for category_name, columns in categories.items():
        # Select only existing columns
        existing_cols = [col for col in columns if col in df.columns]
        
        if existing_cols:
            category_df = df[existing_cols].copy()
            
            # Convert to JSON
            records = category_df.to_dict(orient='records')
            
            # Process records
            processed_records = []
            for record in records:
                processed_record = {}
                for key, value in record.items():
                    processed_record[key] = handle_special_types(value)
                processed_records.append(processed_record)
            
            # Save
            output_file = f'data/processed/wvs_{category_name}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_records, f, indent=2, ensure_ascii=False)
            
            print(f"Created file: {output_file}")

# Run
create_categorized_json(df)
```
### Summary
The next step includes:

 - Downloading files from the WVS website (manual link retrieval + automated downloading)

 - Parsing the downloaded data (extracting from .dta/.sav/.csv formats)

 - Systematizing into JSON files (creating structured representation)
