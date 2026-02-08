from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pathlib import Path
import json

app = FastAPI(title="WVS Backend API", version="0.1.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "wvs_data.json"

def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/data")
def get_data(
    year: Optional[int] = None,
    country: Optional[str] = None,
    region: Optional[str] = None
):
    data = load_data()

    if year is not None:
        data = [d for d in data if d["year"] == year]

    if country is not None:
        data = [d for d in data if d["country"] == country]

    if region is not None:
        data = [d for d in data if d["region"] == region]

    return data

@app.get("/timeseries")
def get_timeseries(country: str):
    data = load_data()

    series = [
        {
            "year": d["year"],
            **d["values"]
        }
        for d in data
        if d["country"] == country
    ]

    return sorted(series, key=lambda x: x["year"])
