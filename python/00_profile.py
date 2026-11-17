"""
00_profile.py - first look at the hotel booking data (no MySQL needed).

What it answers (the five profiling questions from Step 2a of the guide):
  1. How big is the file and what does one row mean?
  2. What period does it cover?
  3. What do the key columns hold (ranges and distinct values)?
  4. What is missing, impossible or odd?
  5. What could give the answer away (leakage) or distort a comparison?

How to run: open this file in VS Code and click the Run triangle (Code Runner).
It reads the CSV from data/hotel_bookings.csv, so the file must be in that folder.
It does not change the CSV. It only reads and prints.
"""

import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# 0. Find and read the file
# ---------------------------------------------------------------------------
# Path(__file__) is this script. .parent.parent goes up to the project folder,
# so the script works wherever you run it from.
DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "hotel_bookings.csv"
csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV

# Read every column as text first. This keeps the original placeholders
# (the word NULL, the letters NA) visible so we can count them, and it makes
# the duplicate check fair, because every column is read the same way.
raw = pd.read_csv(csv_path, dtype=str, keep_default_na=False)


def heading(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ---------------------------------------------------------------------------
# 1. Size and shape. One row = one booking (the file has no booking ID).
# ---------------------------------------------------------------------------
heading("1. Size")
print("rows:", len(raw))
print("columns:", raw.shape[1])
print(list(raw.columns))

# ---------------------------------------------------------------------------
# Make a version with proper types for the numeric checks.
# na_values turns the placeholder words into real missing values.
# ---------------------------------------------------------------------------
df = pd.read_csv(csv_path, na_values=["NULL", "NA"])
df["nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]

# ---------------------------------------------------------------------------
# 2. Hotels and the overall cancellation rate.
# is_canceled is 0 or 1, so its mean is the share of bookings that cancelled.
# ---------------------------------------------------------------------------
heading("2. Hotels and cancellation rate")
by_hotel = df.groupby("hotel")["is_canceled"].agg(bookings="size", cancel_pct="mean")
by_hotel["cancel_pct"] = (by_hotel["cancel_pct"] * 100).round(1)
print(by_hotel.to_string())
print("overall cancellation rate: %.1f%%" % (df["is_canceled"].mean() * 100))

# ---------------------------------------------------------------------------
# 3. Period covered.
# ---------------------------------------------------------------------------
heading("3. Arrival period")
print(df["arrival_date_year"].value_counts().sort_index().to_string())
print("months present in 2015:", sorted(df.loc[df["arrival_date_year"] == 2015, "arrival_date_month"].unique()))
print("months present in 2017:", sorted(df.loc[df["arrival_date_year"] == 2017, "arrival_date_month"].unique()))

# ---------------------------------------------------------------------------
# 4. Ranges of key number columns. Look for impossible or extreme values.
# ---------------------------------------------------------------------------
heading("4. Ranges of number columns")
print(df[["lead_time", "adr", "nights", "adults", "children", "babies"]].describe().round(1).to_string())

# ---------------------------------------------------------------------------
# 5. Placeholder text and missing values.
# ---------------------------------------------------------------------------
heading("5. Placeholders and missing values")
for col in ["agent", "company", "country"]:
    print("%s: %d rows contain the text NULL" % (col, (raw[col] == "NULL").sum()))
print("children: %d rows contain the text NA" % (raw["children"] == "NA").sum())

# ---------------------------------------------------------------------------
# 6. Impossible or odd rows.
# ---------------------------------------------------------------------------
heading("6. Odd rows")
print("adr equal to 0:", int((df["adr"] == 0).sum()))
print("adr below 0:", int((df["adr"] < 0).sum()))
print("highest adr:", df["adr"].max())
print("zero nights:", int((df["nights"] == 0).sum()))
print("zero adults:", int((df["adults"] == 0).sum()))

# ---------------------------------------------------------------------------
# 7. Exact duplicate rows. There is no booking ID, so we cannot tell whether
# a copy is a mistake or a real separate booking that looks identical.
# We use `raw` so that every column is compared as the same kind of text.
# ---------------------------------------------------------------------------
heading("7. Exact duplicate rows")
dup = raw.duplicated()
print("extra copies:", int(dup.sum()), "(%.1f%% of rows)" % (dup.mean() * 100))
share = (dup.groupby(raw["market_segment"]).mean() * 100).round(1)
print("\nshare of rows that are copies, by market segment (%):")
print(share.sort_values(ascending=False).to_string())
print("\ncancellation rate, all rows: %.1f%%" % (df["is_canceled"].mean() * 100))
print("cancellation rate, duplicates removed: %.1f%%" % (df.loc[~dup.values, "is_canceled"].mean() * 100))

# ---------------------------------------------------------------------------
# 8. Cancellation rate by channel (market segment).
# ---------------------------------------------------------------------------
heading("8. Channels")
seg = df.groupby("market_segment")["is_canceled"].agg(bookings="size", cancel_pct="mean")
seg["cancel_pct"] = (seg["cancel_pct"] * 100).round(1)
print(seg.sort_values("bookings", ascending=False).to_string())

# ---------------------------------------------------------------------------
# 9. Deposit type. A very high rate here is suspicious.
# ---------------------------------------------------------------------------
heading("9. Deposit type")
dep = df.groupby("deposit_type")["is_canceled"].agg(bookings="size", cancel_pct="mean")
dep["cancel_pct"] = (dep["cancel_pct"] * 100).round(1)
print(dep.to_string())

# ---------------------------------------------------------------------------
# 10. Leakage check. If each reservation_status sits in only one is_canceled
# group, the status column simply records the answer, so never use it to
# predict cancellations.
# ---------------------------------------------------------------------------
heading("10. Does reservation_status give away the answer?")
print(pd.crosstab(df["is_canceled"], df["reservation_status"]).to_string())

print("\nDone. Copy everything above and send it to me.")
