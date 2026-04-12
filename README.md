# World Values Survey Explorer (v2 - SQLite + Historical Events)


<img width="1909" height="898" alt="image" src="https://github.com/user-attachments/assets/6f03b2ac-14f2-4df6-840c-8c137802e5a3" />


Interactive web app for exploring [World Values Survey](https://www.worldvaluessurvey.org/) data across **108 countries** and **7 waves (1981-2022)**.



This version is fully SQLite-based and now includes **historical events per wave/country** shown directly in the detail panel.

## What Is New In This Version

- Core WVS analytics run from `wvs_data.db` (map/trend/distribution/compare).
- Added historical timeline from `wvs_events_final.json`.
- Events are imported into SQLite table `wvs_events` and served from DB.
- Added an in-panel **event type filter** for easier use by new users.
- Added global wave context events (e.g. international events) when country-specific events are missing.

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

## Tech Stack

- Backend: Python, FastAPI, SQLite
- Frontend: HTML, CSS, Vanilla JS
- Charts/Map: Chart.js, D3.js, TopoJSON
- Deployment: Docker / Docker Compose

## Team

Muhammadjon Aslonov
Irina Napalkova
Amaliya Kharisova
