# World Values Survey Explorer (v2 — SQLite)

An interactive web application for exploring and visualizing data from the [World Values Survey](https://www.worldvaluessurvey.org/) (WVS) — covering **108 countries** across **7 survey waves** (1981–2022).

This is the **v2** of the project. The main change: the backend now runs on a **SQLite database** instead of static JSON files, computing all aggregations on-the-fly with SQL queries.

## Features

- **Interactive World Map** — Choropleth map colored by any selected metric. Click a country to drill down.
- **7 Thematic Categories** — Demographics, Values & Happiness, Trust & Institutions, Politics, Social & Cultural, Moral Views, Welzel Indices.
- **42 Metrics** — Each with full descriptions explaining the survey question and scale.
- **Trend Charts** — See how a metric changed over survey waves for any country.
- **Response Distributions** — View how respondents in a country actually answered each question.
- **Country Comparison** — Compare up to 10 countries side-by-side with overlay line charts and Welzel values radar chart.
- **Wave Filter** — View data for a specific survey wave or the latest available.
- **Country Search** — Quickly find any country by name or ISO code.

## Project Structure

```
├── backend/
│   ├── main.py            # FastAPI app — reads from SQLite, computes aggregations via SQL
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── index.html         # Main HTML page
│   ├── css/style.css      # Dark-theme styles
│   └── js/
│       ├── app.js         # Main app logic, state, API calls
│       ├── map.js         # D3.js world map (choropleth + zoom/pan)
│       ├── charts.js      # Chart.js trend & distribution charts
│       └── compare.js     # Country comparison panel
├── json_to_sqlite.py      # Script to generate wvs_data.db from cleaned JSON files
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose config
└── README.md
```

> **Note:** The SQLite database (`wvs_data.db`, ~553 MB) is **not included in the repository** due to GitHub's file size limits. You must generate it before running the app — see [Setup](#setup) below.

## Data Pipeline

Our data went through four stages of processing:

### Stage 1: Raw Survey Data — ~2 GB

We received ~2 GB of raw World Values Survey data in messy format — inconsistent encodings, cryptic column codes (like `Q1`, `S002VS`), and no human-readable labels. A `variable_map.json` was needed to decode column names.

### Stage 2: Decoded JSONL with Ollama — 30 GB

Using a local LLM (Ollama), the raw data was converted into structured JSONL (`dataset.jsonl`). Each of the **884,946** survey responses was decoded into a JSON object with all **726 columns** mapped to human-readable names. The size grew to 30 GB because every row now carries all 726 verbose field names as JSON keys.

### Stage 3: Cleaned & Themed JSON — 909 MB

The 30 GB was cleaned and split into 7 themed JSON files:
- **726 columns → ~6 per theme**: Only the most meaningful variables kept, grouped into 7 themes.
- **Sentinel values removed**: Codes like `-1` ("Don't know"), `-2` ("No answer"), `-5` ("Not asked") stripped as invalid.
- **Null fields stripped** and **short key names** used (`country_code` → `cc`, `wave` → `w`).
- Result: 7 JSON files totaling ~909 MB. These are available on the `loading_json` branch.

### Stage 4: SQLite Database — 553 MB

The `json_to_sqlite.py` script converts the 7 cleaned JSON files into a single SQLite database (`wvs_data.db`) with 7 tables:

| Table | Rows | Columns |
|---|---|---|
| demographics | 884,896 | 10 |
| values_and_happiness | 884,780 | 10 |
| trust_and_institutions | 881,940 | 10 |
| politics | 882,306 | 9 |
| social_and_cultural | 884,883 | 10 |
| moral_views | 881,194 | 10 |
| welzel_indices | 884,774 | 10 |

The backend queries this database directly with SQL — no pre-aggregation step needed. All means, distributions, and trend data are computed on-the-fly.

### Size Summary

| Stage | Size | What |
|---|---|---|
| Raw data | ~2 GB | Messy CSV with cryptic codes |
| Decoded JSONL | 30 GB | 884,946 rows x 726 columns (Ollama) |
| Cleaned JSON | 909 MB | 884,946 rows x ~6 cols x 7 themes |
| SQLite database | 553 MB | Same data, indexed and queryable |

## Setup

### Step 1: Generate the database

The cleaned JSON files (~909 MB) must be available locally. They are on the `loading_json` branch or in the `Clean_data/` folder.

```bash
# Point the script to your cleaned JSON files and generate the database
python3 json_to_sqlite.py
```

This creates `wvs_data.db` (~553 MB) in the project root.

### Step 2: Run the app

#### Option A: Docker (Recommended)

```bash
docker compose up --build
```

#### Option B: Run Locally

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/countries` | List of all 108 countries with codes |
| `GET /api/themes` | Available themes and their metrics |
| `GET /api/waves` | Survey wave numbers and year ranges |
| `GET /api/map/{theme}/{metric}?wave=N` | Map data (mean per country) |
| `GET /api/trend/{theme}/{metric}?countries=USA,DEU` | Trend over waves |
| `GET /api/distribution/{theme}/{metric}/{cc}?wave=N` | Response distribution |
| `GET /api/country/{cc}` | All data for one country |

## Technologies

- **Backend**: Python, FastAPI, Uvicorn, SQLite
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Visualization**: D3.js (world map), Chart.js (charts)
- **Data Processing**: Ollama (LLM for decoding), Python (cleaning & conversion)
- **Deployment**: Docker

## Team

Data Wrangling and Visualization 2026 — Course Project
