"""
FastAPI backend for World Values Survey visualization app.
Loads data from SQLite database on startup and serves it via REST endpoints.
"""

import sqlite3
import json
import html
import re
import difflib
from urllib import request as urlrequest
from collections import defaultdict
from pathlib import Path
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "wvs_data.db"
FRONTEND_DIR = BASE_DIR / "frontend"
EVENTS_PATH = BASE_DIR / "wvs_events_final.json"

# ── Ordinal value → numeric score mappings ──────────────────────────────────
ORDINAL_TO_NUM = {
    "Very happy": 4, "Quite happy": 3, "Not very happy": 2, "Not at all happy": 1,
    "Very good": 4, "Good": 3, "Fair": 2, "Poor": 1, "Very poor": 0,
    "Very important": 4, "Rather important": 3, "Not very important": 2, "Not at all important": 1,
    "A great deal": 4, "Quite a lot": 3, "Not very much": 2, "None at all": 1,
    "Most people can be trusted": 1, "Need to be very careful": 0,
    "Very interested": 4, "Somewhat interested": 3, "Not very interested": 2, "Not at all interested": 1,
    "Fairly good": 3, "Fairly bad": 2, "Very bad": 1,
    "Post-materialist": 3, "Mixed": 2, "Materialist": 1,
    "A religious person": 3, "Not a religious person": 2, "A convinced atheist": 1,
    "Mentioned": 1, "Not mentioned": 0,
    "Important": 1,
    "Never justifiable": 1, "Always justifiable": 10,
    "Satisfied": 10, "Dissatisfied": 1,
    "Not at all": 1,
    "Absolutely important": 10, "Absolutely imporrtant": 10,
    "Incomes should be made more equal": 1,
    "We need larger income differences as incentives": 10,
    "Lower": 1, "Middle": 2, "Upper": 3,
    "Full time": 5, "Part time": 4, "Self employed": 4, "Retired": 3,
    "Housewife": 2, "Students": 2, "Unemployed": 1, "Other": 2,
    "First step": 1, "Second step": 2, "Third step": 3, "Fourth step": 4,
    "Fifth step": 5, "Sixth step": 6, "Seventh step": 7, "Eighth step": 8,
    "Ninth step": 9, "Tenth step": 10,
}

# ── Theme metadata ──────────────────────────────────────────────────────────
THEME_META = {
    "demographics": {
        "name": "Demographics",
        "table": "demographics",
        "metrics": {
            "sex": {"name": "Sex", "type": "categorical"},
            "age": {"name": "Age", "type": "numeric"},
            "edu": {"name": "Education Level", "type": "ordinal"},
            "emp": {"name": "Employment Status", "type": "categorical"},
            "income": {"name": "Income Level (1-10)", "type": "ordinal"},
            "marital": {"name": "Marital Status", "type": "categorical"},
        }
    },
    "values_and_happiness": {
        "name": "Values & Happiness",
        "table": "values_and_happiness",
        "metrics": {
            "happy": {"name": "Happiness", "type": "ordinal"},
            "life_sat": {"name": "Life Satisfaction (1-10)", "type": "scale"},
            "health": {"name": "Health (self-rated)", "type": "ordinal"},
            "freedom": {"name": "Freedom of Choice (1-10)", "type": "scale"},
            "imp_family": {"name": "Importance of Family", "type": "ordinal"},
            "imp_work": {"name": "Importance of Work", "type": "ordinal"},
        }
    },
    "trust_and_institutions": {
        "name": "Trust & Institutions",
        "table": "trust_and_institutions",
        "metrics": {
            "trust": {"name": "Interpersonal Trust", "type": "ordinal"},
            "gov": {"name": "Confidence in Government", "type": "ordinal"},
            "police": {"name": "Confidence in Police", "type": "ordinal"},
            "army": {"name": "Confidence in Armed Forces", "type": "ordinal"},
            "press": {"name": "Confidence in Press", "type": "ordinal"},
            "justice": {"name": "Confidence in Justice System", "type": "ordinal"},
        }
    },
    "politics": {
        "name": "Politics",
        "table": "politics",
        "metrics": {
            "interest": {"name": "Interest in Politics", "type": "ordinal"},
            "lr_scale": {"name": "Left-Right Scale (1-10)", "type": "scale"},
            "sys_demo": {"name": "Democracy as System", "type": "ordinal"},
            "sys_leader": {"name": "Strong Leader as System", "type": "ordinal"},
            "econ_eq": {"name": "Income Equality (1-10)", "type": "scale"},
        }
    },
    "social_and_cultural": {
        "name": "Social & Cultural",
        "table": "social_and_cultural",
        "metrics": {
            "religious": {"name": "Religious Person", "type": "ordinal"},
            "god_imp": {"name": "Importance of God (1-10)", "type": "scale"},
            "nbr_race": {"name": "Wouldn't want neighbor: Different Race", "type": "ordinal"},
            "nbr_immig": {"name": "Wouldn't want neighbor: Immigrants", "type": "ordinal"},
            "nbr_homo": {"name": "Wouldn't want neighbor: Homosexuals", "type": "ordinal"},
            "child_indep": {"name": "Child Quality: Independence", "type": "ordinal"},
        }
    },
    "moral_views": {
        "name": "Moral Views",
        "table": "moral_views",
        "metrics": {
            "bribe": {"name": "Bribery Justifiable (1-10)", "type": "scale"},
            "homo": {"name": "Homosexuality Justifiable (1-10)", "type": "scale"},
            "abort": {"name": "Abortion Justifiable (1-10)", "type": "scale"},
            "divorce": {"name": "Divorce Justifiable (1-10)", "type": "scale"},
            "suicide": {"name": "Suicide Justifiable (1-10)", "type": "scale"},
            "postmat": {"name": "Post-Materialism Index", "type": "ordinal"},
        }
    },
    "welzel_indices": {
        "name": "Welzel Indices",
        "table": "welzel_indices",
        "metrics": {
            "emancip": {"name": "Emancipative Values (0-1)", "type": "numeric"},
            "secular": {"name": "Secular Values (0-1)", "type": "numeric"},
            "autonomy": {"name": "Autonomy (0-1)", "type": "numeric"},
            "equality": {"name": "Equality (0-1)", "type": "numeric"},
            "choice": {"name": "Choice (0-1)", "type": "numeric"},
            "voice": {"name": "Voice (0-1)", "type": "numeric"},
        }
    },
}

CC_TO_NAME = {
    "ALB": "Albania", "DZA": "Algeria", "AND": "Andorra", "ARG": "Argentina",
    "ARM": "Armenia", "AUS": "Australia", "AZE": "Azerbaijan", "BGD": "Bangladesh",
    "BLR": "Belarus", "BOL": "Bolivia", "BIH": "Bosnia Herzegovina",
    "BRA": "Brazil", "BGR": "Bulgaria", "MMR": "Myanmar", "CAN": "Canada",
    "CHL": "Chile", "CHN": "China", "TWN": "Taiwan", "COL": "Colombia",
    "HRV": "Croatia", "CYP": "Cyprus", "CZE": "Czechia", "DOM": "Dominican Rep.",
    "ECU": "Ecuador", "SLV": "El Salvador", "ETH": "Ethiopia", "EST": "Estonia",
    "FIN": "Finland", "FRA": "France", "GEO": "Georgia", "PSE": "Palestine",
    "DEU": "Germany", "GHA": "Ghana", "GRC": "Greece", "GTM": "Guatemala",
    "HTI": "Haiti", "HKG": "Hong Kong", "HUN": "Hungary", "IND": "India",
    "IDN": "Indonesia", "IRN": "Iran", "IRQ": "Iraq", "ISR": "Israel",
    "ITA": "Italy", "JPN": "Japan", "KAZ": "Kazakhstan", "JOR": "Jordan",
    "KEN": "Kenya", "KOR": "South Korea", "KWT": "Kuwait", "KGZ": "Kyrgyzstan",
    "LBN": "Lebanon", "LVA": "Latvia", "LBY": "Libya", "LTU": "Lithuania",
    "MAC": "Macau", "MYS": "Malaysia", "MDV": "Maldives", "MLI": "Mali",
    "MEX": "Mexico", "MNG": "Mongolia", "MDA": "Moldova", "MNE": "Montenegro",
    "MAR": "Morocco", "NLD": "Netherlands", "NZL": "New Zealand",
    "NIC": "Nicaragua", "NGA": "Nigeria", "NOR": "Norway", "PAK": "Pakistan",
    "PER": "Peru", "PHL": "Philippines", "POL": "Poland", "PRI": "Puerto Rico",
    "QAT": "Qatar", "ROU": "Romania", "RUS": "Russia", "RWA": "Rwanda",
    "SAU": "Saudi Arabia", "SRB": "Serbia", "SGP": "Singapore",
    "SVK": "Slovakia", "VNM": "Vietnam", "SVN": "Slovenia", "ZAF": "South Africa",
    "ZWE": "Zimbabwe", "ESP": "Spain", "SWE": "Sweden", "CHE": "Switzerland",
    "TJK": "Tajikistan", "THA": "Thailand", "TTO": "Trinidad and Tobago",
    "TUN": "Tunisia", "TUR": "Turkey", "UGA": "Uganda", "UKR": "Ukraine",
    "MKD": "North Macedonia", "EGY": "Egypt", "GBR": "United Kingdom",
    "TZA": "Tanzania", "USA": "United States", "BFA": "Burkina Faso",
    "URY": "Uruguay", "UZB": "Uzbekistan", "VEN": "Venezuela", "YEM": "Yemen",
    "ZMB": "Zambia", "NIR": "Northern Ireland",
}

CC_TO_NUMERIC = {
    "ALB": "008", "DZA": "012", "AND": "020", "ARG": "032", "ARM": "051",
    "AUS": "036", "AZE": "031", "BGD": "050", "BLR": "112", "BOL": "068",
    "BIH": "070", "BRA": "076", "BGR": "100", "MMR": "104", "CAN": "124",
    "CHL": "152", "CHN": "156", "TWN": "158", "COL": "170", "HRV": "191",
    "CYP": "196", "CZE": "203", "DOM": "214", "ECU": "218", "SLV": "222",
    "ETH": "231", "EST": "233", "FIN": "246", "FRA": "250", "GEO": "268",
    "PSE": "275", "DEU": "276", "GHA": "288", "GRC": "300", "GTM": "320",
    "HTI": "332", "HKG": "344", "HUN": "348", "IND": "356", "IDN": "360",
    "IRN": "364", "IRQ": "368", "ISR": "376", "ITA": "380", "JPN": "392",
    "KAZ": "398", "JOR": "400", "KEN": "404", "KOR": "410", "KWT": "414",
    "KGZ": "417", "LBN": "422", "LVA": "428", "LBY": "434", "LTU": "440",
    "MAC": "446", "MYS": "458", "MDV": "462", "MLI": "466", "MEX": "484",
    "MNG": "496", "MDA": "498", "MNE": "499", "MAR": "504", "NLD": "528",
    "NZL": "554", "NIC": "558", "NGA": "566", "NOR": "578", "PAK": "586",
    "PER": "604", "PHL": "608", "POL": "616", "PRI": "630", "QAT": "634",
    "ROU": "642", "RUS": "643", "RWA": "646", "SAU": "682", "SRB": "688",
    "SGP": "702", "SVK": "703", "VNM": "704", "SVN": "705", "ZAF": "710",
    "ZWE": "716", "ESP": "724", "SWE": "752", "CHE": "756", "TJK": "762",
    "THA": "764", "TTO": "780", "TUN": "788", "TUR": "792", "UGA": "800",
    "UKR": "804", "MKD": "807", "EGY": "818", "GBR": "826", "TZA": "834",
    "USA": "840", "BFA": "854", "URY": "858", "UZB": "860", "VEN": "862",
    "YEM": "887", "ZMB": "894", "NIR": "826",
}

WAVE_LABELS = {
    "1": "1981-1984", "2": "1989-1993", "3": "1994-1998",
    "4": "1999-2004", "5": "2005-2009", "6": "2010-2014", "7": "2017-2022",
}

# ── Cached data (built on startup from SQLite) ─────────────────────────────
countries: list = []
themes: list = []
waves: dict = {}
theme_data: dict = {}  # {theme_id: {metric_id: {cc: {waves: {...}, latest: {...}, latest_wave: N}}}}

app = FastAPI(title="WVS Visualization API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:14b"

METRIC_ALIASES = {
    "happiness": "happy",
    "happy": "happy",
    "income": "income",
    "life satisfaction": "life_sat",
    "life_sat": "life_sat",
    "trust": "trust",
    "democracy": "democracy",
    "government confidence": "gov",
}

EVENT_TYPE_ALIASES = {
    "economic": "economic_crisis",
    "economic_crises": "economic_crisis",
    "regime": "regime_change",
    "regime_change": "regime_change",
    "political": "regime_change",
    "conflict": "conflict",
    "war": "conflict",
    "protest": "protest",
    "election": "election",
    "alliance": "alliance_join",
    "alliance_join": "alliance_join",
    "olympics": "olympics",
    "other": "other",
}

KNOWN_EVENT_TYPES = {
    "alliance_join", "conflict", "economic_crisis", "election",
    "olympics", "other", "protest", "regime_change",
}


class AICompareRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=1200)


class ParsedAIQuery(BaseModel):
    intent: Literal["compare"]
    countries: list[str]
    metrics: list[str]
    waves: str | int | list[int] = "all"
    include_events: bool = True
    event_types: list[str] = []
    chart_type: str = "line_with_annotations"


def build_country_lookup():
    lookup = {}
    for cc, name in CC_TO_NAME.items():
        lookup[cc.lower()] = cc
        lookup[name.lower()] = cc
    lookup.update({
        "usa": "USA",
        "us": "USA",
        "u.s.": "USA",
        "uk": "GBR",
        "u.k.": "GBR",
        "england": "GBR",
        "russian": "RUS",
    })
    return lookup


def build_metric_lookup():
    lookup = {}
    metric_to_theme = {}
    for theme_id, tmeta in THEME_META.items():
        for metric_id, mmeta in tmeta["metrics"].items():
            lookup[metric_id.lower()] = metric_id
            lookup[mmeta["name"].lower()] = metric_id
            metric_to_theme[metric_id] = theme_id
    lookup.update(METRIC_ALIASES)
    return lookup, metric_to_theme


COUNTRY_LOOKUP = build_country_lookup()
METRIC_LOOKUP, METRIC_TO_THEME = build_metric_lookup()
COUNTRY_STOPWORDS = {"and", "with", "wave", "latest", "compare", "metric", "metrics", "happiness", "income"}


def to_numeric(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        if val in ORDINAL_TO_NUM:
            return float(ORDINAL_TO_NUM[val])
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    return None


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def build_countries(conn):
    """Build the countries list from the database."""
    cursor = conn.execute(
        "SELECT cc, w, yr FROM demographics WHERE cc IS NOT NULL AND cc != ''"
    )
    country_waves = defaultdict(set)
    country_years = defaultdict(set)
    for row in cursor:
        cc, w, yr = row["cc"], row["w"], row["yr"]
        if w:
            country_waves[cc].add(w)
        if yr:
            country_years[cc].add(yr)

    result = []
    for cc in sorted(country_waves.keys()):
        result.append({
            "code": cc,
            "name": CC_TO_NAME.get(cc, cc),
            "numeric": CC_TO_NUMERIC.get(cc, ""),
            "waves": sorted(country_waves[cc]),
            "years": sorted(country_years[cc]),
        })
    return result


def build_themes():
    """Build the themes metadata list."""
    result = []
    for tid, tmeta in THEME_META.items():
        metrics = []
        for mid, mmeta in tmeta["metrics"].items():
            metrics.append({"id": mid, "name": mmeta["name"], "type": mmeta["type"]})
        result.append({"id": tid, "name": tmeta["name"], "metrics": metrics})
    return result


def build_theme_data(conn, theme_id):
    """
    Aggregate one theme's data from SQLite.
    Uses SQL GROUP BY to get value distributions, then computes means in Python.
    """
    tmeta = THEME_META[theme_id]
    table = tmeta["table"]
    result = {}

    for metric_id, mmeta in tmeta["metrics"].items():
        # Get distribution: (cc, w, value, count) — much smaller than raw rows
        cursor = conn.execute(
            f'SELECT cc, w, "{metric_id}", COUNT(*) as cnt '
            f'FROM "{table}" '
            f'WHERE "{metric_id}" IS NOT NULL AND "{metric_id}" != \'\' '
            f'GROUP BY cc, w, "{metric_id}"'
        )

        # Build: {cc: {w: {value: count}}}
        grouped = defaultdict(lambda: defaultdict(dict))
        for row in cursor:
            cc, w, val, cnt = row[0], row[1], row[2], row[3]
            grouped[cc][w][val] = cnt

        metric_data = {}
        for cc in sorted(grouped.keys()):
            waves_data = {}
            for w in sorted(grouped[cc].keys()):
                dist_raw = grouped[cc][w]
                n = sum(dist_raw.values())

                # Top 10 values by count
                sorted_dist = dict(
                    sorted(dist_raw.items(), key=lambda x: -x[1])[:10]
                )

                # Compute mean
                total_num = 0.0
                count_num = 0
                for val, cnt in dist_raw.items():
                    num = to_numeric(val)
                    if num is not None:
                        total_num += num * cnt
                        count_num += cnt
                mean = round(total_num / count_num, 3) if count_num > 0 else None

                waves_data[str(w)] = {
                    "n": n,
                    "mean": mean,
                    "dist": sorted_dist,
                }

            if waves_data:
                latest_w = str(max(int(k) for k in waves_data.keys()))
                metric_data[cc] = {
                    "waves": waves_data,
                    "latest": waves_data[latest_w],
                    "latest_wave": int(latest_w),
                }

        result[metric_id] = metric_data
        print(f"    {metric_id}: {len(metric_data)} countries", flush=True)

    return result


def _normalize_country_name(name: str) -> str:
    return (name or "").strip().lower()


def _build_country_name_lookup():
    lookup = {}
    for cc, cname in CC_TO_NAME.items():
        lookup[_normalize_country_name(cname)] = cc

    # Common aliases in historical sources
    lookup.update({
        "united states": "USA",
        "united states of america": "USA",
        "us": "USA",
        "u.s.": "USA",
        "uk": "GBR",
        "u.k.": "GBR",
        "great britain": "GBR",
        "england": "GBR",
        "north macedonia": "MKD",
        "russian federation": "RUS",
        "south korea": "KOR",
        "north korea": "PRK",
        "czech republic": "CZE",
        "taiwan": "TWN",
        "palestinian territories": "PSE",
        "palestinian territory": "PSE",
        "iran": "IRN",
        "vietnam": "VNM",
        "myanmar": "MMR",
    })
    return lookup


def ensure_events_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wvs_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cc TEXT,
            country TEXT,
            wave INTEGER,
            year INTEGER,
            month INTEGER,
            day INTEGER,
            event_type TEXT,
            title TEXT,
            description TEXT,
            source TEXT,
            confidence REAL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wvs_events_cc_wave ON wvs_events(cc, wave)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wvs_events_wave ON wvs_events(wave)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wvs_events_type ON wvs_events(event_type)")


def load_events_into_db(conn):
    ensure_events_table(conn)
    count = conn.execute("SELECT COUNT(*) FROM wvs_events").fetchone()[0]
    if count > 0:
        print(f"  Events table ready: {count} rows already in SQLite", flush=True)
        return

    if not EVENTS_PATH.exists():
        print(f"  Events file not found at {EVENTS_PATH}, skipping events import.", flush=True)
        return

    print(f"  Importing events JSON into SQLite from {EVENTS_PATH}...", flush=True)
    name_to_cc = _build_country_name_lookup()

    with EVENTS_PATH.open("r", encoding="utf-8") as f:
        raw_events = json.load(f)

    rows = []
    for evt in raw_events:
        wave = evt.get("wave_wvs")
        if wave is None:
            continue
        try:
            wave = int(wave)
        except (TypeError, ValueError):
            continue

        country = (evt.get("country") or "").strip() or None
        cc = name_to_cc.get(_normalize_country_name(country or ""))
        rows.append(
            (
                cc,
                country,
                wave,
                evt.get("year"),
                evt.get("month"),
                evt.get("day"),
                evt.get("event_type"),
                html.unescape((evt.get("title") or "").strip()),
                html.unescape((evt.get("description") or "").strip()),
                evt.get("source"),
                evt.get("confidence"),
            )
        )

    conn.executemany(
        """
        INSERT INTO wvs_events
        (cc, country, wave, year, month, day, event_type, title, description, source, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    print(f"  Events imported into SQLite: {len(rows)} rows", flush=True)


def extract_first_json(text: str) -> dict:
    if not text:
        return {}
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    return json.loads(match.group(0))


def parse_prompt_with_llm(prompt: str) -> dict:
    system_prompt = (
        "You are a query parser. Convert user request to STRICT JSON only.\n"
        "Return exactly one object with keys:\n"
        "intent, countries, metrics, waves, include_events, event_types, chart_type.\n"
        "Rules:\n"
        "- intent must be 'compare'.\n"
        "- countries must be array of country names or ISO3 codes.\n"
        "- metrics must be array of metric names or ids.\n"
        "- waves must be 'all' or array of wave numbers.\n"
        "- include_events must be true/false.\n"
        "- event_types must be array (possibly empty).\n"
        "- chart_type must be 'line_with_annotations'.\n"
        "- No markdown, no explanations.\n"
    )
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{system_prompt}\nUser request: {prompt}",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }
    req = urlrequest.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlrequest.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return extract_first_json(data.get("response", ""))


def fallback_parse_prompt(prompt: str) -> dict:
    plow = prompt.lower()
    countries = []
    for key, cc in COUNTRY_LOOKUP.items():
        if key in COUNTRY_STOPWORDS:
            continue
        if len(key) > 2 and re.search(rf"\b{re.escape(key)}\b", plow):
            countries.append(cc)
    metrics = []
    for key, mid in METRIC_LOOKUP.items():
        if len(key) > 2 and re.search(rf"\b{re.escape(key)}\b", plow):
            metrics.append(mid)
    waves = "all"
    wave_matches = re.findall(r"\bwave[s]?\s*([1-7])\b", plow)
    ordinal_wave_matches = re.findall(r"\b([1-7])(st|nd|rd|th)\s+wave\b", plow)
    if wave_matches:
        waves = sorted({int(w) for w in wave_matches})
    elif ordinal_wave_matches:
        waves = sorted({int(w[0]) for w in ordinal_wave_matches})
    include_events = ("event" in plow) or ("history" in plow)
    return {
        "intent": "compare",
        "countries": sorted(set(countries)),
        "metrics": sorted(set(metrics)),
        "waves": waves,
        "include_events": include_events,
        "event_types": [],
        "chart_type": "line_with_annotations",
    }


def extract_prompt_overrides(prompt: str):
    plow = prompt.lower()
    countries = []
    for key, cc in COUNTRY_LOOKUP.items():
        if key in COUNTRY_STOPWORDS:
            continue
        if len(key) > 1 and re.search(rf"\b{re.escape(key)}\b", plow):
            countries.append(cc)
    countries = sorted(set(countries))

    metrics = []
    for key, mid in METRIC_LOOKUP.items():
        if len(key) > 2 and re.search(rf"\b{re.escape(key)}\b", plow):
            metrics.append(mid)
    metrics = sorted(set(metrics))

    # Fuzzy fallback for typo-heavy prompts.
    if not countries:
        tokens = re.findall(r"[a-zA-Z\.]{3,}", plow)
        country_keys = [name.lower() for name in CC_TO_NAME.values()] + [
            "russia", "russian", "united states", "usa", "us", "united kingdom", "uk"
        ]
        for tok in tokens:
            if tok in COUNTRY_STOPWORDS:
                continue
            best_key = None
            best_score = 0.0
            for key in country_keys:
                score = difflib.SequenceMatcher(a=tok, b=key).ratio()
                if score > best_score:
                    best_score = score
                    best_key = key
            if best_key and best_score >= 0.84:
                countries.append(COUNTRY_LOOKUP[best_key])
        countries = sorted(set(countries))

    if not metrics:
        tokens = re.findall(r"[a-zA-Z_]{4,}", plow)
        metric_keys = [k for k in METRIC_LOOKUP.keys() if len(k) >= 4]
        for tok in tokens:
            matches = difflib.get_close_matches(tok, metric_keys, n=1, cutoff=0.72)
            if matches:
                metrics.append(METRIC_LOOKUP[matches[0]])
        metrics = sorted(set(metrics))

    # Country-specific wave requests, e.g. "US 1st wave", "Russia latest wave"
    country_wave_selection = {}
    for cc in countries:
        cname = CC_TO_NAME.get(cc, "").lower()
        aliases = [cc.lower(), cname]
        if cc == "USA":
            aliases.extend(["us", "u.s.", "united states"])
        if cc == "RUS":
            aliases.extend(["russia", "russian"])
        for alias in aliases:
            if not alias:
                continue
            m_ord = re.search(rf"\b{re.escape(alias)}\b.*?\b([1-7])(st|nd|rd|th)\s+wave\b", plow)
            m_num = re.search(rf"\b{re.escape(alias)}\b.*?\bwave\s*([1-7])\b", plow)
            m_latest = re.search(rf"\b{re.escape(alias)}\b.*?\blatest\s+wave\b", plow)
            if m_ord:
                country_wave_selection[cc] = int(m_ord.group(1))
                break
            if m_num:
                country_wave_selection[cc] = int(m_num.group(1))
                break
            if m_latest:
                country_wave_selection[cc] = "latest"
                break

    return {
        "countries": countries,
        "metrics": metrics,
        "country_wave_selection": country_wave_selection,
    }


def normalize_parsed_query(raw: dict):
    countries_in = raw.get("countries") or []
    metrics_in = raw.get("metrics") or []
    unresolved_countries = []
    unresolved_metrics = []

    countries = []
    for c in countries_in:
        cc = COUNTRY_LOOKUP.get(str(c).strip().lower())
        if cc:
            countries.append(cc)
        else:
            unresolved_countries.append(c)
    countries = sorted(set(countries))

    metrics = []
    for m in metrics_in:
        mid = METRIC_LOOKUP.get(str(m).strip().lower())
        if mid:
            metrics.append(mid)
        else:
            unresolved_metrics.append(m)
    metrics = sorted(set(metrics))

    waves_raw = raw.get("waves", "all")
    if isinstance(waves_raw, str) and waves_raw.lower() == "all":
        waves = list(range(1, 8))
    elif isinstance(waves_raw, int):
        waves = [waves_raw] if 1 <= waves_raw <= 7 else []
    elif isinstance(waves_raw, list):
        waves = sorted({int(w) for w in waves_raw if str(w).isdigit() and 1 <= int(w) <= 7})
    else:
        waves = []

    normalized_event_types = []
    for t in (raw.get("event_types") or []):
        key = str(t).strip().lower()
        mapped = EVENT_TYPE_ALIASES.get(key, key)
        if mapped in KNOWN_EVENT_TYPES:
            normalized_event_types.append(mapped)

    normalized = {
        "intent": "compare",
        "countries": countries,
        "metrics": metrics,
        "waves": waves if waves else list(range(1, 8)),
        "include_events": bool(raw.get("include_events", True)),
        "event_types": sorted(set(normalized_event_types)),
        "chart_type": "line_with_annotations",
    }
    return normalized, unresolved_countries, unresolved_metrics


def get_series_points(country_code: str, metric_id: str, selected_waves: list[int]):
    theme_id = METRIC_TO_THEME.get(metric_id)
    if not theme_id:
        return []
    metric_data = theme_data.get(theme_id, {}).get(metric_id, {})
    country_data = metric_data.get(country_code)
    if not country_data:
        return []
    points = []
    for wave in selected_waves:
        wdata = country_data.get("waves", {}).get(str(wave))
        if not wdata:
            points.append({"wave": wave, "mean": None, "n": 0})
        else:
            points.append({"wave": wave, "mean": wdata.get("mean"), "n": wdata.get("n", 0)})
    return points


def latest_wave_for_metric_country(country_code: str, metric_id: str):
    theme_id = METRIC_TO_THEME.get(metric_id)
    if not theme_id:
        return None
    metric_data = theme_data.get(theme_id, {}).get(metric_id, {})
    country_data = metric_data.get(country_code)
    if not country_data:
        return None
    waves_data = country_data.get("waves", {})
    if not waves_data:
        return None
    return max(int(w) for w in waves_data.keys())


def fetch_events_for_wave(conn, cc: str, wave: int, event_types: list[str], limit: int = 3):
    clauses = ["wave = ?", "(cc = ? OR cc IS NULL)"]
    params = [wave, cc]
    if event_types:
        placeholders = ",".join("?" for _ in event_types)
        clauses.append(f"LOWER(event_type) IN ({placeholders})")
        params.extend(event_types)
    query = f"""
        SELECT event_type, title, country, source
        FROM wvs_events
        WHERE {" AND ".join(clauses)}
        ORDER BY cc IS NULL, confidence DESC, id
        LIMIT ?
    """
    params.append(limit)
    rows = conn.execute(query, tuple(params)).fetchall()
    return [dict(r) for r in rows]


def detect_significant_changes(conn, country_code: str, metric_id: str, points: list[dict], event_types: list[str]):
    annotations = []
    previous = None
    for point in points:
        current = point.get("mean")
        if current is None:
            continue
        if previous is None:
            previous = point
            continue
        delta = current - previous["mean"]
        if abs(delta) >= 0.6:
            wave = point["wave"]
            related = fetch_events_for_wave(conn, country_code, wave, event_types, limit=2)
            event_note = "No linked event found"
            if related:
                first = related[0]
                etype = (first.get("event_type") or "event").replace("_", " ")
                event_note = f"{etype}: {first.get('title', '')}"
            direction = "Increase" if delta > 0 else "Drop"
            annotations.append({
                "wave": wave,
                "value": current,
                "country": country_code,
                "metric": metric_id,
                "delta": round(delta, 3),
                "label": f"{direction} in W{wave} ({delta:+.2f}) -> {event_note}",
                "events": related,
            })
        previous = point
    return annotations


def add_event_context_annotation(conn, country_code: str, metric_id: str, points: list[dict], event_types: list[str]):
    for point in points:
        value = point.get("mean")
        if value is None:
            continue
        related = fetch_events_for_wave(conn, country_code, point["wave"], event_types, limit=1)
        if not related:
            continue
        first = related[0]
        etype = (first.get("event_type") or "event").replace("_", " ")
        return {
            "wave": point["wave"],
            "value": value,
            "country": country_code,
            "metric": metric_id,
            "delta": 0,
            "label": f"Wave {point['wave']} context -> {etype}: {first.get('title', '')}",
            "events": related,
        }
    return None


@app.on_event("startup")
def load_data():
    global countries, themes, waves, theme_data

    print(f"Loading data from {DB_PATH}...", flush=True)
    conn = get_db()

    # Countries
    countries = build_countries(conn)
    print(f"  {len(countries)} countries loaded", flush=True)

    # Themes (static metadata)
    themes = build_themes()

    # Waves (static metadata)
    waves = WAVE_LABELS

    # Aggregate each theme from the database
    for theme_id in THEME_META:
        print(f"  Processing {theme_id}...", flush=True)
        theme_data[theme_id] = build_theme_data(conn, theme_id)

    # Historical events
    load_events_into_db(conn)

    conn.close()
    print("Data loaded successfully!", flush=True)


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


@app.get("/api/events/{cc}")
def get_events(cc: str, wave: Optional[int] = None, limit: int = 12, event_type: Optional[str] = None):
    if not any(c["code"] == cc for c in countries):
        raise HTTPException(404, f"Country '{cc}' not found")

    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50

    conn = get_db()
    country_name = CC_TO_NAME.get(cc, "")

    selected_wave = wave
    if selected_wave is None:
        row = conn.execute(
            """
            SELECT MAX(wave) AS max_wave
            FROM wvs_events
            WHERE cc = ? OR cc IS NULL
            """,
            (cc,),
        ).fetchone()
        selected_wave = row["max_wave"] if row and row["max_wave"] is not None else None

    if selected_wave is None:
        conn.close()
        return {"wave": None, "events": [], "global_events": [], "event_types": []}

    type_sql = ""
    params_country = [selected_wave, cc]
    params_global = [selected_wave]
    if event_type:
        type_sql = " AND event_type = ?"
        params_country.append(event_type)
        params_global.append(event_type)

    events_cur = conn.execute(
        f"""
        SELECT year, month, day, wave, country, event_type, title, description, source, confidence
        FROM wvs_events
        WHERE wave = ? AND cc = ? {type_sql}
        ORDER BY year, month, day, id
        LIMIT ?
        """,
        tuple(params_country + [limit]),
    )
    events = [dict(r) for r in events_cur.fetchall()]

    globals_cur = conn.execute(
        f"""
        SELECT year, month, day, wave, country, event_type, title, description, source, confidence
        FROM wvs_events
        WHERE wave = ? AND cc IS NULL {type_sql}
        ORDER BY year, month, day, id
        LIMIT ?
        """,
        tuple(params_global + [min(limit, 8)]),
    )
    globals_for_wave = [dict(r) for r in globals_cur.fetchall()]

    type_rows = conn.execute(
        """
        SELECT DISTINCT event_type
        FROM wvs_events
        WHERE wave = ? AND (cc = ? OR cc IS NULL) AND event_type IS NOT NULL AND event_type != ''
        ORDER BY event_type
        """,
        (selected_wave, cc),
    ).fetchall()
    available_types = [r["event_type"] for r in type_rows]
    conn.close()

    return {
        "wave": selected_wave,
        "events": events[:limit],
        "global_events": globals_for_wave[: min(limit, 6)],
        "total_events": len(events),
        "event_types": available_types,
        "country": country_name,
    }


@app.post("/api/ai/compare")
def ai_compare(req: AICompareRequest):
    raw = {}
    parser_used = "ollama"
    errors = []
    try:
        raw = parse_prompt_with_llm(req.prompt)
    except Exception:
        parser_used = "fallback"
        raw = fallback_parse_prompt(req.prompt)

    normalized, unresolved_countries, unresolved_metrics = normalize_parsed_query(raw)
    overrides = extract_prompt_overrides(req.prompt)
    # Ground country selection to the user prompt to avoid hallucinated countries.
    if overrides["countries"]:
        normalized["countries"] = sorted(set(overrides["countries"]))
    if overrides["metrics"]:
        normalized["metrics"] = sorted(set(normalized["metrics"] + overrides["metrics"]))
    if not normalized["metrics"]:
        normalized["metrics"] = ["happy"]
        errors.append("No metric detected; defaulted to 'happy' (Happiness).")

    try:
        parsed = ParsedAIQuery(**normalized)
    except ValidationError as e:
        return {
            "status": "ok",
            "parser": parser_used,
            "errors": ["Parsed query validation issue. Returning empty result.", str(e)],
            "result": {"waves": [], "series": [], "annotations": []},
        }

    if len(parsed.countries) < 1:
        errors.append("Need at least one country.")
        return {
            "status": "ok",
            "parser": parser_used,
            "errors": errors,
            "result": {"waves": [], "series": [], "annotations": []},
        }

    if len(parsed.countries) == 1 and len(parsed.metrics) < 2:
        errors.append("For one-country mode, provide at least two metrics (or add another country).")
        return {
            "status": "ok",
            "parser": parser_used,
            "errors": errors,
            "result": {"waves": [], "series": [], "annotations": []},
        }

    selected_waves = sorted(set(parsed.waves if isinstance(parsed.waves, list) else list(range(1, 8))))
    country_wave_selection = overrides.get("country_wave_selection", {})
    if country_wave_selection:
        metric_ref = parsed.metrics[0]
        converted = {}
        for cc, val in country_wave_selection.items():
            if val == "latest":
                lw = latest_wave_for_metric_country(cc, metric_ref)
                if lw is not None:
                    converted[cc] = lw
            else:
                converted[cc] = val
        country_wave_selection = converted
        if country_wave_selection:
            selected_waves = sorted(set(country_wave_selection.values()))

    conn = get_db()
    series = []
    annotations = []

    for cc in parsed.countries:
        for metric in parsed.metrics:
            target_waves = selected_waves
            if cc in country_wave_selection:
                target_waves = [country_wave_selection[cc]]
            points = get_series_points(cc, metric, target_waves)
            if not points:
                continue
            series_key = f"{cc}:{metric}"
            series.append({
                "series_key": series_key,
                "country": cc,
                "country_name": CC_TO_NAME.get(cc, cc),
                "metric": metric,
                "metric_name": THEME_META[METRIC_TO_THEME[metric]]["metrics"][metric]["name"],
                "points": points,
            })
            if parsed.include_events:
                annotations.extend(
                    detect_significant_changes(conn, cc, metric, points, parsed.event_types)
                )
                if not any(a["country"] == cc and a["metric"] == metric for a in annotations):
                    fallback_annot = add_event_context_annotation(conn, cc, metric, points, parsed.event_types)
                    if fallback_annot:
                        annotations.append(fallback_annot)

    conn.close()

    if not series:
        errors.append("No data found for selected countries/metrics/waves.")

    return {
        "status": "ok",
        "parser": parser_used,
        "errors": errors,
        "result": {
            "waves": selected_waves,
            "series": series,
            "annotations": annotations[:80],
        },
    }


@app.get("/")
def serve_index():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"detail": "Frontend not built yet."}

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
