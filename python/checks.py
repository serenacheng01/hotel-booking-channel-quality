"""
checks.py - automated data checks for the hotel booking project.

Run it every time you rebuild or reload the data:
    python python/checks.py

It stops with an error message (an AssertionError) the moment something looks wrong,
so a bad load or a changed file cannot slip through. If everything is fine it
prints "All checks passed."

It only reads the CSV. It does not change anything.
"""

from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parent.parent / "data" / "hotel_bookings.csv"

df = pd.read_csv(CSV, na_values=["NULL", "NA"])

# Each line below is one check. If the condition is False, Python stops and
# prints the message after the comma.
assert len(df) == 119_390, f"row count is {len(df)}, expected 119390"
assert df.shape[1] == 32, f"column count is {df.shape[1]}, expected 32"
assert df["is_canceled"].isin([0, 1]).all(), "is_canceled must be 0 or 1"
assert df["lead_time"].ge(0).all(), "negative lead time"
assert df["hotel"].notna().all(), "missing hotel"
assert set(df["hotel"].unique()) == {"City Hotel", "Resort Hotel"}, "unexpected hotel name"

accepted = {"Online TA", "Offline TA/TO", "Direct", "Corporate",
            "Groups", "Complementary", "Aviation", "Undefined"}
found = set(df["market_segment"].unique())
assert found <= accepted, f"unexpected channel values: {found - accepted}"

# The placeholder words must have become real missing values.
assert df["agent"].isna().sum() == 16_340, "agent missing count changed"
assert df["company"].isna().sum() == 112_593, "company missing count changed"

# Odd rows we decided to handle (see the decision log).
assert (df["adr"] < 0).sum() == 1, "number of negative adr rows changed"
assert (df["adr"] == 0).sum() == 1_959, "number of zero adr rows changed"
assert df["adr"].max() == 5_400, "highest adr changed"

# Money columns must not be negative once the one known bad row is excluded.
assert (df.loc[df["adr"] > 0, "adr"] > 0).all()

print("All checks passed.")
