# World Values Survey Explorer

An interactive web application for exploring and visualizing data from the [World Values Survey](https://www.worldvaluessurvey.org/) (WVS) — covering **108 countries** across **7 survey waves** (1981–2022).

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
├── json/                  # Raw cleaned JSON data (from loading_json branch)
├── data/                  # Preprocessed aggregated data for the webapp (~2MB)
├── backend/
│   ├── main.py            # FastAPI application with REST API
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── index.html         # Main HTML page
│   ├── css/style.css      # Dark-theme styles
│   └── js/
│       ├── app.js         # Main app logic, state, API calls
│       ├── map.js         # D3.js world map (choropleth + zoom/pan)
│       ├── charts.js      # Chart.js trend & distribution charts
│       └── compare.js     # Country comparison panel
├── preprocess.py          # Script to regenerate data/ from json/
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose config
└── README.md
```

## Data Pipeline

1. **Raw data** (`json/` folder) — Cleaned World Values Survey data split into 7 thematic JSON files (~900MB total, stored via Git LFS). Contributed in the `loading_json` branch.
2. **Preprocessing** (`preprocess.py`) — Aggregates the raw JSON files into compact summaries (~2MB): per-country, per-wave means, sample sizes, and response distributions.
3. **Backend** (`backend/main.py`) — FastAPI server that loads the preprocessed data into memory and exposes REST API endpoints.
4. **Frontend** (`frontend/`) — Pure HTML/CSS/JS app using D3.js for the map and Chart.js for charts.

## Quick Start

### Option 1: Docker (Recommended)

```bash
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Option 2: Run Locally

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start the server
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

- **Backend**: Python, FastAPI, Uvicorn
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Visualization**: D3.js (world map), Chart.js (charts)
- **Deployment**: Docker

## Team

Data Wrangling and Visualization 2026 — Course Project
