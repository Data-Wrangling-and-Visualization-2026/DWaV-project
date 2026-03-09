"""
FastAPI backend for World Values Survey visualization app.
Loads preprocessed JSON data on startup and serves it via REST endpoints.
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"

countries: list = []
themes: list = []
waves: dict = {}
theme_data: dict = {}

app = FastAPI(title="WVS Visualization API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def load_data():
    global countries, themes, waves, theme_data
    countries = json.loads((DATA_DIR / "countries.json").read_text())
    themes = json.loads((DATA_DIR / "themes.json").read_text())
    waves = json.loads((DATA_DIR / "waves.json").read_text())
    for theme in themes:
        tid = theme["id"]
        path = DATA_DIR / f"{tid}.json"
        if path.exists():
            theme_data[tid] = json.loads(path.read_text())


@app.get("/api/countries")
def get_countries():
    return countries


@app.get("/api/themes")
def get_themes():
    return themes


@app.get("/api/waves")
def get_waves():
    return waves


@app.get("/api/map/{theme_id}/{metric_id}")
def get_map(theme_id: str, metric_id: str, wave: Optional[int] = None):
    td = theme_data.get(theme_id)
    if td is None:
        raise HTTPException(404, f"Theme '{theme_id}' not found")
    metric = td.get(metric_id)
    if metric is None:
        raise HTTPException(404, f"Metric '{metric_id}' not found")
    result = {}
    for cc, cdata in metric.items():
        if wave is not None:
            w = cdata.get("waves", {}).get(str(wave))
            if w:
                result[cc] = {"mean": w.get("mean"), "n": w.get("n"), "latest_wave": wave}
        else:
            latest = cdata.get("latest")
            if latest:
                result[cc] = {
                    "mean": latest.get("mean"),
                    "n": latest.get("n"),
                    "latest_wave": cdata.get("latest_wave"),
                }
    return result


@app.get("/api/country/{cc}")
def get_country(cc: str):
    if not any(c["code"] == cc for c in countries):
        raise HTTPException(404, f"Country '{cc}' not found")
    result = {}
    for theme in themes:
        tid = theme["id"]
        td = theme_data.get(tid)
        if not td:
            continue
        theme_result = {}
        for m in theme["metrics"]:
            mid = m["id"]
            cdata = td.get(mid, {}).get(cc)
            if cdata:
                theme_result[mid] = cdata
        if theme_result:
            result[tid] = theme_result
    return result


@app.get("/api/trend/{theme_id}/{metric_id}")
def get_trend(theme_id: str, metric_id: str, countries_param: str = Query(..., alias="countries")):
    td = theme_data.get(theme_id)
    if not td:
        raise HTTPException(404, f"Theme '{theme_id}' not found")
    metric = td.get(metric_id)
    if not metric:
        raise HTTPException(404, f"Metric '{metric_id}' not found")
    codes = [c.strip() for c in countries_param.split(",") if c.strip()]
    result = {}
    for cc in codes:
        cdata = metric.get(cc)
        if not cdata:
            result[cc] = []
            continue
        wlist = []
        for wnum, wdata in sorted(cdata.get("waves", {}).items(), key=lambda x: int(x[0])):
            wlist.append({"wave": int(wnum), "mean": wdata.get("mean"), "n": wdata.get("n"), "dist": wdata.get("dist")})
        result[cc] = wlist
    return result


@app.get("/api/distribution/{theme_id}/{metric_id}/{cc}")
def get_distribution(theme_id: str, metric_id: str, cc: str, wave: Optional[int] = None):
    td = theme_data.get(theme_id)
    if not td:
        raise HTTPException(404)
    metric = td.get(metric_id)
    if not metric:
        raise HTTPException(404)
    cdata = metric.get(cc)
    if not cdata:
        raise HTTPException(404, f"No data for {cc}")
    if wave is not None:
        wdata = cdata.get("waves", {}).get(str(wave))
        if not wdata:
            raise HTTPException(404)
        return {"wave": wave, "n": wdata.get("n"), "mean": wdata.get("mean"), "dist": wdata.get("dist")}
    latest = cdata.get("latest", {})
    return {"wave": cdata.get("latest_wave"), "n": latest.get("n"), "mean": latest.get("mean"), "dist": latest.get("dist")}


@app.get("/")
def serve_index():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"detail": "Frontend not built yet."}

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
