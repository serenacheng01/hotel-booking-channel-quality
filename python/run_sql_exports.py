"""
run_sql_exports.py - run the queries in sql/03_channel_quality.sql and write
each result to a CSV, so nobody has to export nine files by hand in DBeaver.

How it works: every query in the SQL file has a comment line like
    -- Export as: 03_q1a_channel_quality.csv
just above it. This script reads the file, runs each query that follows such a
comment, and saves the result under that name in the sql/ folder.

How to run (MySQL must be running, and steps 1 and 2 must have been done):
    python python/run_sql_exports.py

It prints each file name with its row count. The CSVs it writes should be
identical to the ones exported by hand; python/04_pandas_channel_analysis.py
then compares its own results against them.
"""

import re
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

PROJECT = Path(__file__).resolve().parent.parent
SQL_FILE = PROJECT / "sql" / "03_channel_quality.sql"
OUT_DIR = PROJECT / "sql"


def split_queries(sql_text):
    """Return (file_name, statement) pairs for every query marked 'Export as:'."""
    pairs, buffer, current = [], [], None
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            m = re.search(r"Export as:\s*(\S+\.csv)", stripped)
            if m:
                current = m.group(1)
            continue
        if not stripped and not buffer:
            continue
        # drop trailing comments on code lines
        code = re.sub(r"\s--.*$", "", line)
        buffer.append(code)
        if code.rstrip().endswith(";"):
            statement = "\n".join(buffer).strip().rstrip(";")
            if current:
                pairs.append((current, statement))
            buffer, current = [], None
    return pairs


def main():
    engine = get_engine()
    queries = split_queries(SQL_FILE.read_text())
    assert len(queries) == 9, f"expected 9 exported queries, found {len(queries)}"
    with engine.connect() as conn:
        for name, statement in queries:
            result = pd.read_sql(text(statement), conn)
            result.to_csv(OUT_DIR / name, index=False)
            print(f"{name:45s} {len(result):4d} rows")
    print("Done. Now run: python python/04_pandas_channel_analysis.py")


if __name__ == "__main__":
    main()
