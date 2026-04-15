# World Values Survey Explorer (v3 - SQLite + Historical Events)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![SQLite](https://img.shields.io/badge/SQLite-3.x-lightblue)
![Docker](https://img.shields.io/badge/Docker-28.0+-blue)





Interactive web app for exploring [World Values Survey](https://www.worldvaluessurvey.org/) data across **108 countries** and **7 waves (1981-2022)**.



This version is fully SQLite-based and now includes **historical events per wave/country** shown directly in the detail panel.

<img width="1899" height="903" alt="image" src="https://github.com/user-attachments/assets/ab6d762a-85d2-420a-9a37-c0fae1516c19" />

## What Is New In This Version

- Core WVS analytics run from `wvs_data.db` (map/trend/distribution/compare).
- Added historical timeline from `wvs_events_final.json`.
- Events are imported into SQLite table `wvs_events` and served from DB.
- Added an in-panel **event type filter** for easier use by new users.
- Added global wave context events (e.g. international events) when country-specific events are missing.
- Added **AI-Powered Comparison** — ask natural language questions (e.g., "Compare happiness and income for Poland and Germany") and get charts with historical event annotations.
- Added **welcome modal** with feature explanation for first-time users.

## Features

- Interactive world choropleth map by selected metric.
- 7 themes and 40+ metrics with descriptions and scale guidance.
- Country detail panel:
  - Trend across waves
  - Response distribution
  - Historical events for selected wave
  - Event type filter
- Country comparison (line + Welzel radar).
- Wave selector (specific wave or latest).
- Fast country search.
- Compare up to **10 countries** simultaneously (trend line chart + Welzel radar)
- **AI-Powered Comparison** — type any question in natural language, AI parses it and returns comparison charts with detected historical event explanations.
- **Welcome modal** — shows available features and example queries when the app first loads.

## Project Structure

```text
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── map.js
│       ├── charts.js
│       └── compare.js
├── json_to_sqlite.py
├── wvs_events_final.json
├── Dockerfile
├── docker-compose.yml
├── wvs_data.db
└── README.md
```

## Database

Primary SQLite database file: `wvs_data.db` (~580 MB)

- Download link: [DWaV database (Google Drive)](https://drive.google.com/drive/folders/1r1kX32NKC0Tx9SCo3kmC4VZgXkHJ3e4k?usp=sharing)

Place `wvs_data.db` in the project root (`DWaV-v3/`).

## Setup

1. Download `wvs_data.db` from:
   [DWaV database (Google Drive)](https://drive.google.com/drive/folders/1r1kX32NKC0Tx9SCo3kmC4VZgXkHJ3e4k?usp=sharing)
2. Put it into project root.
3. Run app (Docker or local).

### Prerequisites

- Docker Desktop (for containerized run) OR
- Python 3.11+ with pip (for local run)
- 1 GB free disk space (for database + Docker images)

### Run the app

#### Docker

```bash
docker compose up --build
```

#### Local

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

## Historical Events Behavior

- On backend startup, `wvs_events` table is created if missing.
- If `wvs_events` is empty and `wvs_events_final.json` exists, events are imported automatically.
- After import, events are read from SQLite (the app can run without JSON file if DB already has events).


## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/countries` | Country metadata |
| `GET /api/themes` | Themes and metrics |
| `GET /api/waves` | Wave labels |
| `GET /api/map/{theme}/{metric}?wave=N` | Map means per country |
| `GET /api/trend/{theme}/{metric}?countries=USA,DEU` | Wave trends |
| `GET /api/distribution/{theme}/{metric}/{cc}?wave=N` | Distribution for one country |
| `GET /api/events/{cc}?wave=N&event_type=TYPE&limit=24` | Historical events for country + global context |
| `GET /api/country/{cc}` | Full country data |

## AI-Powered Comparison & Explanation

This version adds an **AI Comparison** feature that allows you to ask natural language questions about happiness, income, and other WVS metrics across countries and waves.

### How It Works

1. You type a question in natural language
2. Backend sends your query to an LLM 
3. LLM returns a structured JSON (countries, metrics, waves, required analysis)
4. Backend validates the JSON and fetches real data from SQLite
5. Frontend displays the results

### What You See After the Query

- **Comparison Chart** — displays trends for the requested countries and metrics across all waves with historical event annotations
- **Detected Change Explanations** — shows historical events that match the selected country, wave, and metric

### Example Questions to Ask

- *"Compare happiness and income for Poland and Germany across all waves and explain major changes using historical events"*
- *"Compare Russians' happiness and interest in politics"*
- *"Compare Tajikistan and Uzbekistan in health and show historical events"*
- *"Compare Brazil and Uganda happiness"*
- *"Compare happiness and income of Italy and Tajikistan"*

### Requirements

- Ollama with a model like `qwen2.5:14b` 
- Configure the API URL in backend settings (default: `http://localhost:11434` for Ollama)

  

### API Endpoints for AI

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/compare` | POST | Send natural language query, get structured comparison with event explanations |


## Configuration

Optional environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |


## Tech Stack

- Backend: Python, FastAPI, SQLite
- Frontend: HTML, CSS, Vanilla JS
- Charts/Map: Chart.js, D3.js, TopoJSON
- Deployment: Docker / Docker Compose

## Data Sources

- **World Values Survey** — official survey data (waves 1-7, 1981-2022)
- **Historical events** — scraped from Wikipedia (country-specific and global events for each wave period)
- **Welzel indices** — calculated based on Christian Welzel's methodology (2013)

## Team

- Muhammadjon Aslonov
- Irina Napalkova
- Amaliya Kharisova
