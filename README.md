
# 🌍 World Values Survey Explorer (v3 — SQLite + Historical Events)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![SQLite](https://img.shields.io/badge/SQLite-3.x-lightblue)
![Docker](https://img.shields.io/badge/Docker-28.0+-blue)

Interactive web app for exploring data from the World Values Survey across **108 countries** and **7 waves (1981–2022)**.

This version is fully SQLite-based and now includes **historical events per wave/country** shown directly in the detail panel.
<img width="1899" height="903" alt="image" src="https://github.com/user-attachments/assets/ab6d762a-85d2-420a-9a37-c0fae1516c19" />

---

## ✨ What Is New In This Version

- Core WVS analytics run from `wvs_data.db` (map / trend / distribution / compare)
- Added historical timeline from `wvs_events_final.json`
- Events are imported into SQLite table `wvs_events` and served from DB
- Added an in-panel **event type filter**
- Added global wave context events when country-specific events are missing
- Added **AI-Powered Comparison** 🤖
- Added **welcome modal** for first-time users

---

## 🧭 Features

- Interactive world choropleth map by selected metric
- 7 themes and 40+ metrics with descriptions
- Country detail panel:
  - Trend across waves 📈
  - Response distribution
  - Historical events 🗓️
  - Event type filter
- Country comparison (line + Welzel radar)
- Wave selector
- Fast country search 🔎
- Compare up to **10 countries**
- **AI-Powered Comparison** with historical explanations

---

## 📁 Project Structure

```

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

````

---

## 🗄️ Database

Primary SQLite database file: `wvs_data.db` (~580 MB)

Download link:  
https://drive.google.com/drive/folders/1r1kX32NKC0Tx9SCo3kmC4VZgXkHJ3e4k?usp=sharing

Place `wvs_data.db` in the project root.

---

## ⚙️ Setup

### Prerequisites

- Docker Desktop **or** Python 3.11+
- ~10 GB free disk space
- Ollama with model:

```bash
ollama pull qwen2.5:14b
````

### Run with Docker

```bash
docker compose up --build
```

### Run locally

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open: [http://localhost:8000](http://localhost:8000)

---

## 🗓️ Historical Events Behavior

* On startup, `wvs_events` table is created if missing
* If empty and JSON exists, events are imported automatically
* Afterwards, events are read from SQLite

---

## 🔌 API Endpoints

| Endpoint                                           | Description           |
| -------------------------------------------------- | --------------------- |
| `/api/countries`                                   | Country metadata      |
| `/api/themes`                                      | Themes and metrics    |
| `/api/waves`                                       | Wave labels           |
| `/api/map/{theme}/{metric}?wave=N`                 | Map means per country |
| `/api/trend/{theme}/{metric}?countries=USA,DEU`    | Wave trends           |
| `/api/distribution/{theme}/{metric}/{cc}?wave=N`   | Distribution          |
| `/api/events/{cc}?wave=N&event_type=TYPE&limit=24` | Historical events     |
| `/api/country/{cc}`                                | Full country data     |
| `/api/ai/compare`                                  | AI-powered comparison |

---

## 🤖 AI-Powered Comparison

Ask natural language questions like:

* "Compare happiness and income for Poland and Germany"
* "Compare Russians' happiness and interest in politics"
* "Compare Brazil and Uganda happiness"

The app:

1. Sends query to LLM
2. Gets structured JSON
3. Fetches real data from SQLite
4. Displays charts with event explanations

---

## 🔧 Configuration (optional)

| Variable | Default   | Description |
| -------- | --------- | ----------- |
| `HOST`   | `0.0.0.0` | Server host |
| `PORT`   | `8000`    | Server port |

---

## 🧱 Tech Stack

* Backend: Python, FastAPI, SQLite
* Frontend: HTML, CSS, Vanilla JS
* Charts/Map: Chart.js, D3.js, TopoJSON
* Deployment: Docker / Docker Compose

---

## 📚 Data Sources

* World Values Survey (waves 1–7)
* Historical events from Wikipedia
* Welzel indices (2013 methodology)

---

## 👥 Team

* Muhammadjon Aslonov
* Irina Napalkova
* Amaliya Kharisova

```
```
