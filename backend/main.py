"""
FastAPI backend for World Values Survey visualization app.
Loads data from SQLite database on startup and serves it via REST endpoints.
"""

import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "wvs_data.db"
FRONTEND_DIR = BASE_DIR / "frontend"

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


@app.get("/")
def serve_index():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"detail": "Frontend not built yet."}

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
