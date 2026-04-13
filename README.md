# World Values Survey Explorer (v4)

Interactive web app for exploring [World Values Survey](https://www.worldvaluessurvey.org/) data across **108 countries** and **7 waves (1981-2022)**.

## What Changed

- SQLite-first backend (`wvs_data.db`) for map/trend/distribution/comparison data.
- Historical events integrated and stored in SQLite table `wvs_events`.
- AI Comparison tab (natural language -> structured query -> validated DB fetch).
- Intro/welcome page shown before entering the app; reopen anytime with `About` button.
- Improved prompt handling for typos and shorthand (for countries/metrics/waves).

## Features

- Interactive map explorer with theme/metric/wave filters.
- Country detail panel:
  - trend chart,
  - response distribution,
  - historical events + event type filter.
- Classic country comparison panel (trend + Welzel radar).
- AI-powered comparison and explanation tab with event annotations.
- Country search and wave filtering.

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
│       ├── compare.js
│       └── ai_compare.js
├── Dockerfile
├── docker-compose.yml
├── json_to_sqlite.py
├── wvs_events_final.json
├── wvs_data.db
└── README.md
```

## Data Files

- Main DB: `wvs_data.db` (~580 MB)
- Events source: `wvs_events_final.json` (imported into SQLite automatically if needed)
- Database download: [DWaV database (Google Drive)](https://drive.google.com/drive/folders/1r1kX32NKC0Tx9SCo3kmC4VZgXkHJ3e4k?usp=sharing)

## Run Guide (Windows / Linux / macOS)

### 1) Prerequisites

- Python 3.10+ (recommended 3.11)
- `pip`
- Optional: Docker Desktop / Docker Engine
- Optional (for AI tab): [Ollama](https://ollama.com/download)

### 2) Place database

Put `wvs_data.db` in repository root.

### 3) Run with Docker (all OS)

```bash
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000).

### 4) Run locally (Windows/macOS/Linux)

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

### 5) Enable AI comparison tab (optional)

Install and run Ollama, then pull model:

```bash
ollama pull qwen2.5:14b
ollama serve
```

AI endpoint uses `qwen2.5:14b` by default.

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/countries` | Country metadata |
| `GET /api/themes` | Themes and metrics |
| `GET /api/waves` | Wave labels |
| `GET /api/map/{theme}/{metric}?wave=N` | Map means per country |
| `GET /api/trend/{theme}/{metric}?countries=USA,DEU` | Wave trends |
| `GET /api/distribution/{theme}/{metric}/{cc}?wave=N` | Distribution for one country |
| `GET /api/events/{cc}?wave=N&event_type=TYPE&limit=24` | Historical events (country + global context) |
| `POST /api/ai/compare` | AI prompt-based comparison |

## Tech Stack

- Backend: Python, FastAPI, SQLite
- Frontend: HTML, CSS, vanilla JavaScript
- Visualization: D3.js, Chart.js
- Deployment: Docker

## Team

Data Wrangling and Visualization 2026 - Course Project
