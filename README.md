# DWaV Project – WVS Data Visualization

Backend + Frontend application for interactive visualization of **World Values Survey (WVS)** data.


<img width="1909" height="898" alt="image" src="https://github.com/user-attachments/assets/d01e0192-eb84-4f98-a09a-4dc39523c663" />



### Source

**Link:** [www.worldvaluessurvey.org](https://www.worldvaluessurvey.org/WVSOnline.jsp)
**DOI**: 10.14281/18241.27.


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





---

## Next Steps: Data Loading and Systematization into JSON

### 1. Download Data from WVS Website

The downloaded files will include survey data in various formats (Stata .dta, SPSS .sav, or CSV), along with accompanying documentation and codebooks.

### 2. Parse the Downloaded Data

Once the files are downloaded, they need to be parsed — meaning extracting the structured data and converting it into a workable format for analysis:

- **Extract archives:** Unzip any compressed files to access the raw data
- **Load into pandas:** Import the data from its original format (Stata, SPSS, or CSV) into a pandas DataFrame
- **Initial inspection:** Check basic information about the dataset — number of rows, columns, and data types
- **Handle encoding:** Ensure proper text encoding for international survey responses

### 3. Systematize Data into JSON Files

The most important step is transforming the parsed data into structured JSON files. JSON (JavaScript Object Notation) is chosen because it's:

- **Human-readable:** Easy to inspect and understand
- **Language-independent:** Can be used with any programming language
- **Hierarchical:** Can represent complex nested structures
- **Web-friendly:** Easily consumed by web applications and APIs


### 4. Create Categorized JSON Files

For more convenient analysis, the data will be split into multiple thematic JSON files. This categorization makes it easier to work with specific aspects of the survey without loading the entire dataset:

- **Values file:** Includes questions about trust, religion, politics, and family values
- **Wellbeing file:** Covers happiness, life satisfaction, and health-related questions
- **Country statistics file:** Aggregates data at the country level

Each file will contain only relevant variables, making them smaller and more focused for specific analytical tasks.


### Summary

The next phase encompasses three main activities:

1. **Downloading** files from the WVS website — a combination of manual link retrieval and automated downloading
2. **Parsing** the downloaded data — extracting from original formats (.dta, .sav, .csv) into a workable DataFrame
3. **Systematizing** into JSON files — creating a structured, categorized representation of the data

Upon completion of these steps, the World Values Survey data will be transformed from raw downloadable files into a well-organized, documented, and easily accessible JSON format, ready for subsequent analysis and visualization tasks.


