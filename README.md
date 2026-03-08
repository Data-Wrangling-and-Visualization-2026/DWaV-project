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




# World Values Survey — Cleaned Dataset

## Source
- **Original**: `dataset.jsonl` (30 GB, 884,946 rows, 726 columns)
- **Survey**: World Values Survey (WVS), waves 1–7 (1981–2022), 108 countries

## What Was Cleaned
1. **Removed sentinel/placeholder values**: `VOICE2- Welzel voice-2`, `-1` to `-5`, `"Not asked"`, `"Not asked in survey"`, `"No answer"`, `"Don't know"`, `"Missing; Unknown"`, `"Missing; Not available"`, `"Not applicable"`
2. **Stripped null fields** from JSON (if a respondent wasn't asked a question, that key is simply absent from their row)
3. **Selected 42 most visualization-worthy columns** from the original 726
4. **Sorted** alphabetically by country code (ALB → ZWE), then by wave (1–7), then by survey year

## Files (908 MB total)

| File | Size | Rows | Description |
|------|------|------|-------------|
| `demographics.json` | 110 MB | 884,896 | Sex, age, education, employment, income, marital status |
| `values_and_happiness.json` | 134 MB | 884,780 | Happiness, life satisfaction, health, freedom, family/work importance |
| `trust_and_institutions.json` | 141 MB | 881,940 | Interpersonal trust, confidence in government/police/army/press/justice |
| `politics.json` | 130 MB | 882,306 | Political interest, left-right scale, democracy views, economic equality |
| `social_and_cultural.json` | 156 MB | 884,883 | Religiosity, god importance, neighbor tolerance, child qualities |
| `moral_views.json` | 131 MB | 881,194 | Justifiability of bribery/homosexuality/abortion/divorce/suicide, post-materialism |
| `welzel_indices.json` | 107 MB | 884,774 | Emancipative values, secular values, autonomy/equality/choice/voice indices |
| `codebook.json` | <1 KB | — | Maps short column names to original WVS variable names |

## Key Columns (present in every file)

| Key | Meaning | Example |
|-----|---------|---------|
| `cc` | 3-letter ISO country code | `"ALB"`, `"USA"`, `"JPN"` |
| `w` | WVS wave number (1–7) | `3` |
| `yr` | Year the survey was conducted | `"1998"` |

## Column Reference by File

### demographics.json
| Column | Meaning |
|--------|---------|
| `sex` | Male / Female |
| `age` | Age in years |
| `edu` | Education level (Lower / Middle / Upper) |
| `emp` | Employment status (Full time, Part time, Self employed, Retired, Students, etc.) |
| `income` | Subjective income level (10-step scale: First step to Tenth step) |
| `marital` | Marital status (Married, Single/Never married, Divorced, Widowed, etc.) |

### values_and_happiness.json
| Column | Meaning |
|--------|---------|
| `happy` | Feeling of happiness (Very happy / Quite happy / Not very happy / Not at all happy) |
| `life_sat` | Satisfaction with life (1 = Dissatisfied → 10 = Satisfied) |
| `health` | Subjective state of health (Very good / Good / Fair / Poor) |
| `freedom` | How much freedom of choice and control (1 = None at all → 10 = A great deal) |
| `imp_family` | Importance of family in life (Very / Rather / Not very / Not at all important) |
| `imp_work` | Importance of work in life (same scale) |

### trust_and_institutions.json
| Column | Meaning |
|--------|---------|
| `trust` | Most people can be trusted vs. need to be very careful |
| `gov` | Confidence in the government (A great deal / Quite a lot / Not very much / None at all) |
| `police` | Confidence in the police (same scale) |
| `army` | Confidence in the armed forces (same scale) |
| `press` | Confidence in the press (same scale) |
| `justice` | Confidence in the justice system/courts (same scale) |

### politics.json
| Column | Meaning |
|--------|---------|
| `interest` | Interest in politics (Very / Somewhat / Not very / Not at all interested) |
| `lr_scale` | Left-right self-positioning (1 = Left → 10 = Right) |
| `democracy` | How important is it to live in a democracy (1 = Not at all → 10 = Absolutely important) |
| `sys_demo` | Having a democratic political system (Very good / Fairly good / Fairly bad / Very bad) |
| `sys_leader` | Having a strong leader who doesn't bother with parliament (same scale) |
| `econ_eq` | Income equality preference (Incomes should be made more equal ↔ We need larger income differences) |

### social_and_cultural.json
| Column | Meaning |
|--------|---------|
| `religious` | A religious person / Not a religious person / A convinced atheist |
| `god_imp` | How important is God in your life (1 = Not at all → 10 = Very important) |
| `nbr_race` | Would not like as neighbors: people of a different race (Mentioned / Not mentioned) |
| `nbr_immig` | Would not like as neighbors: immigrants/foreign workers (Mentioned / Not mentioned) |
| `nbr_homo` | Would not like as neighbors: homosexuals (Mentioned / Not mentioned) |
| `child_indep` | Important child quality: independence (Important / Not mentioned) |

### moral_views.json
| Column | Meaning |
|--------|---------|
| `bribe` | Is accepting a bribe justifiable (1 = Never → 10 = Always justifiable) |
| `homo` | Is homosexuality justifiable (same scale) |
| `abort` | Is abortion justifiable (same scale) |
| `divorce` | Is divorce justifiable (same scale) |
| `suicide` | Is suicide justifiable (same scale) |
| `postmat` | Post-materialist index (Materialist / Mixed / Post-materialist) |

### welzel_indices.json
| Column | Meaning |
|--------|---------|
| `emancip` | Welzel emancipative values index (0–1 scale) |
| `secular` | Welzel overall secular values (0–1 scale) |
| `autonomy` | Welzel autonomy sub-index (0–1 scale) |
| `equality` | Welzel equality sub-index (0–1 scale) |
| `choice` | Welzel choice sub-index (0–1 scale) |
| `voice` | Welzel voice sub-index (0–1 scale) |

## Row Counts Differ Slightly Between Files
Not every respondent was asked every question. Rows where ALL theme-specific columns would be null are excluded from that file. The key columns (`cc`, `w`, `yr`) link rows across files.

## How to Use

```python
import json

with open("clean/demographics.json") as f:
    demo = json.load(f)

# All Albanian respondents
albania = [r for r in demo if r["cc"] == "ALB"]

# Wave 7 (2017-2022) data only
wave7 = [r for r in demo if r.get("w") == 7]
```

```javascript
// In a web app
fetch("clean/values_and_happiness.json")
  .then(r => r.json())
  .then(data => {
    const happy = data.filter(r => r.happy === "Very happy");
    console.log(`${happy.length} very happy respondents`);
  });
```
