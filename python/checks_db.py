"""
checks_db.py - automated checks on the DATABASE (the raw table and the view),
the way checks.py checks the CSV.

Run it after steps 1 and 2 and again whenever you change the view:
    python python/checks_db.py

It stops with an error message at the first thing that looks wrong. If all is
well it prints "All database checks passed."
"""

import pandas as pd
from sqlalchemy import text

from db import get_engine

engine = get_engine()


def scalar(sql):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


# Tables and row counts
assert scalar("SELECT COUNT(*) FROM bookings") == 119_390, "bookings should have 119,390 rows"
assert scalar("SELECT COUNT(*) FROM v_bookings_clean") == 117_430, "view should have 117,430 rows"

# The measures
assert scalar("SELECT COUNT(*) FROM v_bookings_clean WHERE booked_revenue < 0") == 0, \
    "negative booked revenue"
assert scalar("SELECT COUNT(*) FROM v_bookings_clean WHERE realised_revenue > booked_revenue") == 0, \
    "realised revenue above booked revenue"
assert scalar("SELECT COUNT(*) FROM v_bookings_clean "
              "WHERE is_canceled = 1 AND realised_revenue <> 0") == 0, \
    "a cancelled booking has realised revenue"
assert scalar("SELECT COUNT(*) FROM v_bookings_clean "
              "WHERE is_canceled = 0 AND realised_revenue <> booked_revenue") == 0, \
    "a kept booking has realised revenue different from booked revenue"

# The channels add up to the whole view, and only known channels appear
by_channel = pd.read_sql(
    text("SELECT market_segment, COUNT(*) AS n FROM v_bookings_clean GROUP BY market_segment"),
    engine.connect())
assert by_channel["n"].sum() == 117_430, "channel counts do not add up to the view"
known = {"Direct", "Corporate", "Online TA", "Offline TA/TO", "Complementary",
         "Groups", "Aviation", "Undefined"}
assert set(by_channel["market_segment"]) <= known, "unexpected channel name"

# Headline figures used in the memo (from my own run)
assert scalar("SELECT COUNT(*) FROM v_bookings_clean WHERE market_segment = 'Online TA'") == 56_110
assert round(scalar("SELECT SUM(booked_revenue - realised_revenue) FROM v_bookings_clean "
                    "WHERE market_segment = 'Online TA'")) == 10_227_646, \
    "Online TA revenue at risk differs from the memo"

print("All database checks passed.")
