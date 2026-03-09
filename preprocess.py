#!/usr/bin/env python3
"""
Preprocess cleaned WVS data into small aggregated JSON files for the webapp.
Reads each themed JSON file (~100-150MB), aggregates by country+wave,
and saves compact summary files (~5-10MB each).
"""

import json
import os
import sys
from collections import defaultdict

CLEAN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")

# ── Ordinal value → numeric score mappings ──────────────────────────────────
# Used to compute means for choropleth map coloring
ORDINAL_TO_NUM = {
    # Happiness (4-point)
    "Very happy": 4, "Quite happy": 3, "Not very happy": 2, "Not at all happy": 1,
    # Health
    "Very good": 4, "Good": 3, "Fair": 2, "Poor": 1, "Very poor": 0,
    # Importance (family, work, religion, etc.)
    "Very important": 4, "Rather important": 3, "Not very important": 2, "Not at all important": 1,
    # Confidence in institutions
    "A great deal": 4, "Quite a lot": 3, "Not very much": 2, "None at all": 1,
    # Trust
    "Most people can be trusted": 1, "Need to be very careful": 0,
    # Political interest
    "Very interested": 4, "Somewhat interested": 3, "Not very interested": 2, "Not at all interested": 1,
    # Political system rating
    "Very good": 4, "Fairly good": 3, "Fairly bad": 2, "Very bad": 1,
    # Post-materialist
    "Post-materialist": 3, "Mixed": 2, "Materialist": 1,
    # Religious person
    "A religious person": 3, "Not a religious person": 2, "A convinced atheist": 1,
    # Neighbors (Mentioned = would NOT want as neighbor → higher = less tolerant)
    "Mentioned": 1, "Not mentioned": 0,
    # Child qualities
    "Important": 1,
    # Justifiability scale endpoints
    "Never justifiable": 1, "Always justifiable": 10,
    # Life satisfaction / Freedom / Democracy endpoints
    "Satisfied": 10, "Dissatisfied": 1,
    "A great deal": 10, "Not at all": 1,
    "Absolutely important": 10, "Absolutely imporrtant": 10,  # typo in data
    # Income equality
    "Incomes should be made more equal": 1,
    "We need larger income differences as incentives": 10,
    # Education
    "Lower": 1, "Middle": 2, "Upper": 3,
    # Employment (not truly ordinal, but useful)
    "Full time": 5, "Part time": 4, "Self employed": 4, "Retired": 3,
    "Housewife": 2, "Students": 2, "Unemployed": 1, "Other": 2,
    # Income steps
    "First step": 1, "Second step": 2, "Third step": 3, "Fourth step": 4,
    "Fifth step": 5, "Sixth step": 6, "Seventh step": 7, "Eighth step": 8,
    "Ninth step": 9, "Tenth step": 10,
}

# ── Theme metadata: human-readable names and metric types ───────────────────
THEME_META = {
    "demographics": {
        "name": "Demographics",
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
        "metrics": {
            "interest": {"name": "Interest in Politics", "type": "ordinal"},
            "lr_scale": {"name": "Left-Right Scale (1-10)", "type": "scale"},
            "democracy": {"name": "Importance of Democracy (1-10)", "type": "scale"},
            "sys_demo": {"name": "Democracy as System", "type": "ordinal"},
            "sys_leader": {"name": "Strong Leader as System", "type": "ordinal"},
            "econ_eq": {"name": "Income Equality (1-10)", "type": "scale"},
        }
    },
    "social_and_cultural": {
        "name": "Social & Cultural",
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

# ── ISO Alpha-3 → Country Name mapping ─────────────────────────────────────
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

# ISO Alpha-3 → ISO Numeric (for matching TopoJSON world-atlas features)
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

WAVE_LABELS = {1: "1981-1984", 2: "1989-1993", 3: "1994-1998",
               4: "1999-2004", 5: "2005-2009", 6: "2010-2014", 7: "2017-2022"}


def to_numeric(val):
    """Try to convert a value to a number for aggregation."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        # Check ordinal map
        if val in ORDINAL_TO_NUM:
            return float(ORDINAL_TO_NUM[val])
        # Try parsing as number
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    return None


def process_theme(theme_id):
    """Load a theme JSON and compute aggregated statistics."""
    path = os.path.join(CLEAN_DIR, f"{theme_id}.json")
    print(f"\n  Loading {theme_id}.json ...", end=" ", flush=True)

    with open(path) as f:
        rows = json.load(f)
    print(f"{len(rows):,} rows")

    meta = THEME_META[theme_id]
    metric_ids = list(meta["metrics"].keys())

    # Collect data grouped by country and wave
    # Structure: {metric: {cc: {wave: [values]}}}
    grouped = {m: defaultdict(lambda: defaultdict(list)) for m in metric_ids}

    for row in rows:
        cc = row.get("cc")
        w = row.get("w")
        if not cc or not w:
            continue
        for m in metric_ids:
            val = row.get(m)
            if val is not None:
                grouped[m][cc][w].append(val)

    del rows  # free memory

    # Compute aggregates
    result = {}
    for m in metric_ids:
        mtype = meta["metrics"][m]["type"]
        metric_data = {}

        for cc in sorted(grouped[m].keys()):
            waves_data = {}
            for w in sorted(grouped[m][cc].keys()):
                values = grouped[m][cc][w]
                n = len(values)

                # Distribution (top 10 values)
                dist = defaultdict(int)
                for v in values:
                    dist[str(v)] = dist.get(str(v), 0) + 1
                # Sort by count descending, keep top 10
                sorted_dist = dict(sorted(dist.items(), key=lambda x: -x[1])[:10])

                # Numeric mean
                nums = [to_numeric(v) for v in values]
                nums = [x for x in nums if x is not None]
                mean = round(sum(nums) / len(nums), 3) if nums else None

                # Get most common year for this wave
                waves_data[str(w)] = {
                    "n": n,
                    "mean": mean,
                    "dist": sorted_dist,
                }

            # Overall (latest available wave)
            latest_w = str(max(int(k) for k in waves_data.keys()))
            metric_data[cc] = {
                "waves": waves_data,
                "latest": waves_data[latest_w],
                "latest_wave": int(latest_w),
            }

        result[m] = metric_data
        print(f"    {m}: {len(metric_data)} countries")

    return result


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # ── 1. Countries list ───────────────────────────────────────────────
    print("Building countries list...")
    # Get actual country list from one of the data files
    with open(os.path.join(CLEAN_DIR, "demographics.json")) as f:
        demo = json.load(f)

    country_waves = defaultdict(set)
    country_years = defaultdict(set)
    for row in demo:
        cc = row.get("cc")
        w = row.get("w")
        yr = row.get("yr")
        if cc:
            if w:
                country_waves[cc].add(w)
            if yr:
                country_years[cc].add(yr)
    del demo

    countries = []
    for cc in sorted(country_waves.keys()):
        countries.append({
            "code": cc,
            "name": CC_TO_NAME.get(cc, cc),
            "numeric": CC_TO_NUMERIC.get(cc, ""),
            "waves": sorted(country_waves[cc]),
            "years": sorted(country_years[cc]),
        })

    with open(os.path.join(OUT_DIR, "countries.json"), "w") as f:
        json.dump(countries, f, separators=(",", ":"))
    print(f"  countries.json: {len(countries)} countries")

    # ── 2. Themes metadata ──────────────────────────────────────────────
    themes = []
    for tid, tmeta in THEME_META.items():
        metrics = []
        for mid, mmeta in tmeta["metrics"].items():
            metrics.append({"id": mid, "name": mmeta["name"], "type": mmeta["type"]})
        themes.append({"id": tid, "name": tmeta["name"], "metrics": metrics})

    with open(os.path.join(OUT_DIR, "themes.json"), "w") as f:
        json.dump(themes, f, separators=(",", ":"))
    print(f"  themes.json: {len(themes)} themes")

    # ── 3. Wave labels ──────────────────────────────────────────────────
    with open(os.path.join(OUT_DIR, "waves.json"), "w") as f:
        json.dump(WAVE_LABELS, f, separators=(",", ":"))

    # ── 4. Process each theme ───────────────────────────────────────────
    print("\nProcessing themes...")
    for theme_id in THEME_META:
        data = process_theme(theme_id)
        out_path = os.path.join(OUT_DIR, f"{theme_id}.json")
        with open(out_path, "w") as f:
            json.dump(data, f, separators=(",", ":"))
        size_mb = os.path.getsize(out_path) / (1024 ** 2)
        print(f"  -> {out_path} ({size_mb:.1f} MB)")

    # ── Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    total = sum(
        os.path.getsize(os.path.join(OUT_DIR, f))
        for f in os.listdir(OUT_DIR)
    )
    print(f"Total data size: {total / (1024**2):.1f} MB")
    for f in sorted(os.listdir(OUT_DIR)):
        s = os.path.getsize(os.path.join(OUT_DIR, f))
        print(f"  {f:.<40s} {s / (1024**2):>6.1f} MB")
    print("Done!")


if __name__ == "__main__":
    main()
