"""
06_timing_and_adjusted.py - Step 4b: three questions the first pass left open.

  A. WHEN do cancellations happen? (decides when a reminder could help)
  B. Is Online TA really worse than Direct, or is that just a different mix of
     hotel and lead time? (like-for-like comparison)
  C. How big must a reminder's effect be to pay for itself, and how does that
     compare with what the test can detect? (break-even and sample size)

It also adds 95% intervals to the channel table and flags groups that are too
small to quote.

Why this file exists: the first memo said the data does not show WHEN a
booking was cancelled. That was wrong. The column reservation_status_date is
the date the last status was set, so for a cancelled booking it is the date of
cancellation (TidyTuesday data dictionary). This script uses it.

How to run: python python/06_timing_and_adjusted.py
Needs: data/hotel_bookings.csv. Writes tables and charts into results/.
It never changes the raw CSV.
"""

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
CSV = PROJECT / "data" / "hotel_bookings.csv"
OUT = PROJECT / "results"
OUT.mkdir(exist_ok=True)

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}
MIN_GROUP = 200          # my own cut-off, same as step 4
SMALL_GROUP = 1000       # below this, intervals are wide: flag the row


def heading(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def wilson(k, n, z=1.96):
    """95% interval for a share (Wilson), returned as percentages."""
    p = k / n
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return 100 * (centre - half) / d, 100 * (centre + half) / d


# ---------------------------------------------------------------------------
# 1. Load and clean (same decisions as the SQL view and as step 4)
# ---------------------------------------------------------------------------
heading("1. Load and clean")
raw = pd.read_csv(CSV, dtype=str, keep_default_na=False)
is_copy = raw.duplicated().to_numpy()

df = pd.read_csv(CSV, na_values=["NULL", "NA"])
df["is_copy"] = is_copy
df["nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
df["booked_revenue"] = df["adr"] * df["nights"]
df["realised_revenue"] = np.where(df["is_canceled"] == 0, df["booked_revenue"], 0.0)
df["revenue_at_risk"] = df["booked_revenue"] - df["realised_revenue"]

# Dates. Arrival date is built from three columns; the cancellation date is
# reservation_status_date (for a cancelled booking, the day it was cancelled).
df["arrival"] = pd.to_datetime(dict(
    year=df["arrival_date_year"],
    month=df["arrival_date_month"].map(MONTHS),
    day=df["arrival_date_day_of_month"]))
df["status_date"] = pd.to_datetime(df["reservation_status_date"])
df["days_before_arrival"] = (df["arrival"] - df["status_date"]).dt.days
df["days_after_booking"] = df["lead_time"] - df["days_before_arrival"]

v = df[df["adr"] > 0].copy()   # the same filter as the SQL view
assert len(v) == 117_430, f"expected 117430 rows, got {len(v)}"
print("rows after the adr > 0 filter:", len(v))

# Sanity checks on the dates before using them.
canc = v[v["is_canceled"] == 1]
assert (canc["days_before_arrival"] >= 0).all(), "cancellation after arrival?"
assert (canc["days_after_booking"] >= 0).all(), "cancellation before booking?"
print("cancelled bookings:", len(canc),
      "of which No-Show:", int((canc["reservation_status"] == "No-Show").sum()))

v["lead_band"] = pd.cut(
    v["lead_time"], [-1, 7, 30, 90, 180, 10**6],
    labels=["1: 0-7 days", "2: 8-30 days", "3: 31-90 days",
            "4: 91-180 days", "5: 181+ days"])

# ---------------------------------------------------------------------------
# A. When do cancellations happen? (test group: Online TA, No Deposit, 91+ days)
# ---------------------------------------------------------------------------
heading("A. When do cancellations happen in the test group?")
tg = v[(v["market_segment"] == "Online TA")
       & (v["deposit_type"] == "No Deposit")
       & (v["lead_time"] > 90)]
tgc = tg[tg["is_canceled"] == 1]
assert len(tg) == 20_673 and len(tgc) == 9_884, "test group does not match the memo"
print(f"test group: {len(tg)} bookings, {len(tgc)} cancelled "
      f"({100 * len(tgc) / len(tg):.1f}%)")
print("No-Show among the cancelled:", int((tgc["reservation_status"] == "No-Show").sum()))

edges_before = [-1, 7, 14, 30, 60, 90, 180, 10**6]
labels_before = ["0-7", "8-14", "15-30", "31-60", "61-90", "91-180", "181+"]
edges_after = [-1, 0, 7, 14, 30, 60, 90, 10**6]
labels_after = ["same day", "1-7", "8-14", "15-30", "31-60", "61-90", "91+"]

before = pd.cut(tgc["days_before_arrival"], edges_before, labels=labels_before)
after = pd.cut(tgc["days_after_booking"], edges_after, labels=labels_after)
t_before = (before.value_counts(sort=False) / len(tgc) * 100).round(1)
t_after = (after.value_counts(sort=False) / len(tgc) * 100).round(1)
timing = pd.concat([
    pd.DataFrame({"measure": "days before arrival", "band": t_before.index,
                  "pct_of_cancellations": t_before.values}),
    pd.DataFrame({"measure": "days after booking", "band": t_after.index,
                  "pct_of_cancellations": t_after.values}),
])
print("\nCancellations by days BEFORE arrival (% of cancellations):")
print(t_before.to_string())
print("\nCancellations by days AFTER booking (% of cancellations):")
print(t_after.to_string())
timing.to_csv(OUT / "06_timing_test_group.csv", index=False)

# What share of eventual cancellations is still ahead when a message goes out?
reach_rows = []
for d in [0, 3, 7, 14, 30, 60]:
    reach_rows.append({
        "message_sent_days_after_booking": d,
        "pct_of_cancellations_still_to_come":
            round(100 * (tgc["days_after_booking"] > d).mean(), 1)})
reach = pd.DataFrame(reach_rows)
print("\nShare of cancellations that happen AFTER a message sent on day d:")
print(reach.to_string(index=False))
reach.to_csv(OUT / "06_reach_by_message_day.csv", index=False)

for d in [14, 30]:
    print(f"cancelled at least {d} days before arrival: "
          f"{100 * (tgc['days_before_arrival'] >= d).mean():.1f}%")
print("median days after booking:", int(tgc["days_after_booking"].median()),
      "| median days before arrival:", int(tgc["days_before_arrival"].median()))

# ---------------------------------------------------------------------------
# B. Like-for-like: Online TA vs Direct at the same hotel and lead time
# ---------------------------------------------------------------------------
heading("B. Online TA vs Direct, same hotel and lead-time band")


def standardised(frame, target, source):
    """Cancellation rate of `target` if it had the hotel x lead-band mix of `source`."""
    cells = (frame.groupby(["market_segment", "hotel", "lead_band"], observed=True)
             .agg(n=("is_canceled", "size"), rate=("is_canceled", "mean")).reset_index())
    w = cells[cells["market_segment"] == source].set_index(["hotel", "lead_band"])["n"]
    r = cells[cells["market_segment"] == target].set_index(["hotel", "lead_band"])["rate"]
    joined = pd.concat([w.rename("w"), r.rename("r")], axis=1).dropna()
    return 100 * (joined["w"] * joined["r"]).sum() / joined["w"].sum()


rows = []
for label, frame in [("all rows", v), ("identical rows removed", v[~v["is_copy"]])]:
    rows.append({
        "data": label,
        "online_ta_actual": round(100 * frame.loc[frame.market_segment == "Online TA", "is_canceled"].mean(), 1),
        "direct_actual": round(100 * frame.loc[frame.market_segment == "Direct", "is_canceled"].mean(), 1),
        "online_ta_with_direct_mix": round(standardised(frame, "Online TA", "Direct"), 1),
        "direct_with_online_ta_mix": round(standardised(frame, "Direct", "Online TA"), 1)})
lfl = pd.DataFrame(rows)
print(lfl.to_string(index=False))
lfl.to_csv(OUT / "06_like_for_like.csv", index=False)

cells = (v.groupby(["hotel", "lead_band", "market_segment"], observed=True)
         .agg(n=("is_canceled", "size"), rate=("is_canceled", "mean")).reset_index())
piv = cells.pivot_table(index=["hotel", "lead_band"], columns="market_segment",
                        values=["n", "rate"], observed=True)
gap = pd.DataFrame({
    "online_ta_bookings": piv["n"]["Online TA"],
    "direct_bookings": piv["n"]["Direct"],
    "online_ta_cancel_pct": (100 * piv["rate"]["Online TA"]).round(1),
    "direct_cancel_pct": (100 * piv["rate"]["Direct"]).round(1)})
gap["gap_points"] = (gap["online_ta_cancel_pct"] - gap["direct_cancel_pct"]).round(1)
gap = gap[(gap["online_ta_bookings"] >= MIN_GROUP) & (gap["direct_bookings"] >= MIN_GROUP)]
print("\nGap in cancellation rate (Online TA minus Direct), groups of 200+ each:")
print(gap.to_string())
gap.reset_index().to_csv(OUT / "06_online_ta_vs_direct_gap.csv", index=False)

# ---------------------------------------------------------------------------
# Channel table with 95% intervals; flag groups that are too small
# ---------------------------------------------------------------------------
heading("Channel table with 95% intervals")
ch = (v.groupby("market_segment")
      .agg(bookings=("is_canceled", "size"), cancelled=("is_canceled", "sum"),
           revenue_at_risk=("revenue_at_risk", "sum")).reset_index())
ch["cancel_pct"] = (100 * ch["cancelled"] / ch["bookings"]).round(1)
ci = [wilson(k, n) for k, n in zip(ch["cancelled"], ch["bookings"])]
ch["ci_low"] = [round(a, 1) for a, _ in ci]
ch["ci_high"] = [round(b, 1) for _, b in ci]
ch["share_of_bookings_pct"] = (100 * ch["bookings"] / ch["bookings"].sum()).round(1)
ch["share_of_risk_pct"] = (100 * ch["revenue_at_risk"] / ch["revenue_at_risk"].sum()).round(1)
ch["small_group_flag"] = np.where(ch["bookings"] < SMALL_GROUP, "too small to quote", "")
ch = ch.sort_values("revenue_at_risk", ascending=False)
print(ch.to_string(index=False))
ch.to_csv(OUT / "06_channel_quality_with_intervals.csv", index=False)

# ---------------------------------------------------------------------------
# C. Break-even and sample size
# ---------------------------------------------------------------------------
heading("C. Break-even and sample size")
avg_kept = tgc["booked_revenue"].mean()
print(f"average booked revenue of a cancelled booking in the test group: {avg_kept:.1f}")

be_rows = []
for commission in [0.0, 0.10, 0.15, 0.20]:       # ASSUMED, not in the data
    net = avg_kept * (1 - commission)
    for cost in [0.25, 0.50, 1.00, 2.00]:        # ASSUMED cost per treated booking
        be_rows.append({"assumed_commission": f"{int(commission * 100)}%",
                        "revenue_kept_per_saved_booking": round(net, 1),
                        "assumed_cost_per_treated_booking": cost,
                        "break_even_drop_points": round(100 * cost / net, 2)})
be = pd.DataFrame(be_rows)
print(be[be["assumed_cost_per_treated_booking"] == 1.00].to_string(index=False))
be.to_csv(OUT / "06_break_even.csv", index=False)


def n_per_group(p1, drop, z_a=1.96, z_b=0.8416):
    """Bookings per group, two proportions, 80% power, 5% two-sided (pooled variance)."""
    p2 = p1 - drop
    pbar = (p1 + p2) / 2
    num = (z_a * sqrt(2 * pbar * (1 - pbar)) + z_b * sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return num / drop ** 2


base = len(tgc) / len(tg)
months_in_file = 26
per_month = len(tg) / months_in_file
ss_rows = []
for drop in [0.05, 0.03, 0.02, 0.01]:
    n = int(round(n_per_group(base, drop)))
    ss_rows.append({"drop_points": int(drop * 100), "bookings_per_group": n,
                    "total": 2 * n, "months_at_historical_volume": round(2 * n / per_month, 1)})
ss = pd.DataFrame(ss_rows)
print(f"\nbaseline cancellation rate {100 * base:.1f}%, about {per_month:.0f} bookings a month")
print(ss.to_string(index=False))
ss.to_csv(OUT / "06_sample_size.csv", index=False)
n_be = n_per_group(base, 0.0018)
print(f"\nbookings per group needed to detect the break-even drop of 0.18 points: {n_be:,.0f}")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
heading("Charts")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
ax[0].bar(labels_before, t_before.values, color="#4e79a7")
ax[0].set_title("Days before arrival", loc="left", fontsize=11)
ax[1].bar(labels_after, t_after.values, color="#e8590c")
ax[1].set_title("Days after booking", loc="left", fontsize=11)
for a in ax:
    a.set_ylabel("% of cancellations")
    a.spines[["top", "right"]].set_visible(False)
    for p in a.patches:
        a.annotate(f"{p.get_height():.0f}%", (p.get_x() + p.get_width() / 2, p.get_height()),
                   ha="center", va="bottom", fontsize=9)
fig.suptitle("When Online TA no-deposit bookings made 91+ days ahead are cancelled "
             "(9,884 cancellations)", x=0.01, ha="left", fontsize=12)
fig.tight_layout()
fig.savefig(OUT / "06_chart_cancellation_timing.png", dpi=160)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.6))
for hotel, colour in [("City Hotel", "#4e79a7"), ("Resort Hotel", "#e8590c")]:
    g = gap.xs(hotel, level="hotel")
    ax.plot(g.index.astype(str), g["gap_points"], marker="o", label=hotel, color=colour)
ax.axhline(0, color="#999", lw=0.8)
ax.set_ylabel("Online TA minus Direct (percentage points)")
ax.set_title("Online TA cancels more than Direct, and the gap grows with lead time",
             loc="left", fontsize=11)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "06_chart_online_ta_vs_direct_gap.png", dpi=160)
plt.close(fig)
print("Saved 2 charts and 7 tables to the results folder. Done.")
