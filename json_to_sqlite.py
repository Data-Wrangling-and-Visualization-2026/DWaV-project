#!/usr/bin/env python3
"""
Convert cleaned JSON files (from Clean_data/) into a single SQLite database.

Input:  7 themed JSON files (~900 MB total, ~884,946 rows each)
Output: wvs_data.db — one table per theme + a combined view joining all tables

Usage:
    python json_to_sqlite.py /path/to/Clean_data
    python json_to_sqlite.py              # defaults to ../Clean_data
"""

import json
import os
import sqlite3
import sys
import time

THEMES = [
    "demographics",
    "values_and_happiness",
    "trust_and_institutions",
    "politics",
    "social_and_cultural",
    "moral_views",
    "welzel_indices",
]

COMMON_COLS = ["cc", "w", "yr"]

DB_NAME = "wvs_data.db"


def stream_json_rows(filepath):
    """Stream rows from a JSON array file without loading it all into memory."""
    with open(filepath, "r") as f:
        f.readline()  # skip opening [
        for line in f:
            line = line.strip().rstrip(",").strip()
            if not line or line == "]":
                continue
            yield json.loads(line)


def create_table(cursor, table_name, columns):
    """Create a table with the given columns. All values stored as TEXT."""
    col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    cursor.execute(f"CREATE TABLE {table_name} (row_id INTEGER PRIMARY KEY, {col_defs})")


def insert_rows(conn, table_name, columns, filepath):
    """Insert all rows from a JSON file into the table."""
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

    cursor = conn.cursor()
    batch = []
    count = 0

    for row in stream_json_rows(filepath):
        values = tuple(str(row.get(c, "")) if row.get(c) is not None else None for c in columns)
        batch.append(values)
        count += 1

        if len(batch) >= 50000:
            cursor.executemany(sql, batch)
            conn.commit()
            print(f"  {table_name}: {count:,} rows inserted...", flush=True)
            batch = []

    if batch:
        cursor.executemany(sql, batch)
        conn.commit()

    print(f"  {table_name}: {count:,} rows total — done.", flush=True)
    return count


def create_combined_view(cursor):
    """Create a view that joins all theme tables on row_id."""
    # Get non-common columns from each theme table
    select_parts = ["d.row_id", "d.cc", "d.w", "d.yr"]

    for theme in THEMES:
        cursor.execute(f"PRAGMA table_info({theme})")
        cols = [row[1] for row in cursor.fetchall()]
        alias = theme[0] if theme != "trust_and_institutions" else "ti"
        if theme == "social_and_cultural":
            alias = "sc"
        elif theme == "moral_views":
            alias = "mv"
        elif theme == "values_and_happiness":
            alias = "vh"
        elif theme == "welzel_indices":
            alias = "wi"
        elif theme == "politics":
            alias = "p"
        elif theme == "demographics":
            alias = "d"

        for c in cols:
            if c not in COMMON_COLS and c != "row_id":
                select_parts.append(f"{alias}.{c}")

    joins = []
    aliases = {
        "demographics": "d",
        "values_and_happiness": "vh",
        "trust_and_institutions": "ti",
        "politics": "p",
        "social_and_cultural": "sc",
        "moral_views": "mv",
        "welzel_indices": "wi",
    }

    for theme in THEMES[1:]:
        alias = aliases[theme]
        joins.append(f"LEFT JOIN {theme} {alias} ON d.row_id = {alias}.row_id")

    sql = f"""
    CREATE VIEW IF NOT EXISTS all_data AS
    SELECT {', '.join(select_parts)}
    FROM demographics d
    {chr(10).join(joins)}
    """
    cursor.execute("DROP VIEW IF EXISTS all_data")
    cursor.execute(sql)


def main():
    clean_data_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Clean_data")
    clean_data_dir = os.path.abspath(clean_data_dir)

    if not os.path.isdir(clean_data_dir):
        print(f"Error: directory not found: {clean_data_dir}")
        sys.exit(1)

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)
    print(f"Source:  {clean_data_dir}")
    print(f"Output:  {db_path}")
    print()

    # Remove existing DB
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Performance settings for bulk insert
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA cache_size = -200000")  # 200MB cache

    start = time.time()

    for theme in THEMES:
        filepath = os.path.join(clean_data_dir, f"{theme}.json")
        if not os.path.exists(filepath):
            print(f"  WARNING: {filepath} not found, skipping.")
            continue

        # Get columns from first row
        row = next(stream_json_rows(filepath))
        columns = list(row.keys())

        print(f"\nProcessing {theme}...")
        create_table(cursor, theme, columns)
        insert_rows(conn, theme, columns, filepath)

        # Create index on common columns
        cursor.execute(f"CREATE INDEX idx_{theme}_cc_w ON {theme}(cc, w)")

    # Create combined view
    print("\nCreating combined view 'all_data'...")
    create_combined_view(cursor)

    conn.commit()
    conn.close()

    elapsed = time.time() - start
    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"\nDone in {elapsed:.1f}s — {db_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
