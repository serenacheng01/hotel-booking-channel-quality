"""
01_load.py - load the hotel booking CSV into MySQL.

Before you run it:
  1. In DBeaver, create an empty database called hotel_bookings.
  2. Create a file called .env in the project folder (next to requirements.txt)
     with these three lines, using your own MySQL details:
         MYSQL_USER=your_user
         MYSQL_PASSWORD=your_password
         MYSQL_HOST=localhost
     Never share this file or upload it to GitHub (.gitignore already excludes it).
  3. Check that data/hotel_bookings.csv exists.

What it does:
  - reads the CSV and turns the placeholder words NULL and NA into real missing values
  - writes one table called bookings (replacing any earlier copy, so it is safe to rerun)
  - counts the rows in MySQL and stops with an error if they do not match the CSV

The raw CSV is never changed.
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Project folder = one level above this script's folder.
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Read MYSQL_USER, MYSQL_PASSWORD and MYSQL_HOST from the .env file.
load_dotenv(PROJECT_DIR / ".env")

CSV = PROJECT_DIR / "data" / "hotel_bookings.csv"

# Build the connection to MySQL. "mysql+pymysql" names the driver we installed.
engine = create_engine(
    f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
    f"@{os.environ.get('MYSQL_HOST', 'localhost')}/hotel_bookings"
)

# Read the file. In this data the words NULL (agent, company, country) and NA
# (four rows of children) stand for "missing", so we turn them into real blanks.
df = pd.read_csv(CSV, na_values=["NULL", "NA"])

# agent, company and children are whole numbers that can be missing.
# "Int64" (capital I) is the pandas type that allows that.
for col in ["agent", "company", "children"]:
    df[col] = df[col].astype("Int64")

# Write the table. if_exists="replace" drops and recreates it, so reruns are safe.
df.to_sql("bookings", engine, if_exists="replace", index=False, chunksize=10000)

# Check that every row arrived.
with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM bookings")).scalar()

print("rows in CSV:  ", len(df))
print("rows in MySQL:", n)
assert n == len(df), "row count in MySQL does not match the CSV"
print("Load complete.")
