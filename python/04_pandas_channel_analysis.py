"""
04_pandas_channel_analysis.py - Step 4: repeat the SQL findings in pandas,
then build a simple risk grouping.

What it does, in order:
  1. Load and clean the CSV with the SAME decisions as the SQL.
  2. Reproduce Query 1a (channel table) with groupby and compare it with the
     CSV you exported from MySQL. If they differ, it tells you which rows.
  3. Build lead-time bands with pd.cut (same bands as Query 2) and compare.
  4. Repeat the channel table with identical rows removed (Query 1c).
  5. Build a simple risk grouping: lead-time band x deposit type x channel.
  6. Save result tables and two charts into the results/ folder.

How to run: python python/04_pandas_channel_analysis.py
Needs: data/hotel_bookings.csv and the CSVs from Step 3 in the sql/ folder.
It never changes the raw CSV.
"""

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
CSV = PROJECT / "data" / "hotel_bookings.csv"
SQL_DIR = PROJECT / "sql"
OUT = PROJECT / "results"
OUT.mkdir(exist_ok=True)


def heading(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ---------------------------------------------------------------------------
# 1. Load and clean
# ---------------------------------------------------------------------------
heading("1. Load and clean")

# Read everything as text once, only to find identical rows. As text, every
# column is compared the same way, so the count matches the SQL (31,994).
raw = pd.read_csv(CSV, dtype=str, keep_default_na=False)
is_copy = raw.duplicated().to_numpy()

# The real working table: NULL and NA become proper missing values.
df = pd.read_csv(CSV, na_values=["NULL", "NA"])
for col in ["agent", "company", "children"]:
    df[col] = df[col].astype("Int64")

# The measures, defined exactly as in the SQL view v_bookings_clean.
df["nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
df["booked_revenue"] = df["adr"] * df["nights"]
df["realised_revenue"] = np.where(df["is_canceled"] == 0, df["booked_revenue"], 0.0)
df["revenue_at_risk"] = df["booked_revenue"] - df["realised_revenue"]

print("rows loaded:", len(df))
print("identical extra copies:", int(is_copy.sum()), "(SQL gave 31994)")

# Decision from the SQL: drop rows with adr <= 0 (zero or negative rate).
clean = df[df["adr"] > 0].copy()
print("rows after adr > 0 filter:", len(clean), "(SQL view gave 117430)")
assert len(clean) == 117_430, "filtered row count differs from the SQL view"

# ---------------------------------------------------------------------------
# 2. Reproduce Query 1a with groupby
# ---------------------------------------------------------------------------
heading("2. Channel table, reproduced with groupby (Query 1a)")


def channel_table(data):
    g = data.groupby("market_segment")
    t = pd.DataFrame({
        "bookings": g.size(),
        "cancel_pct": (g["is_canceled"].mean() * 100).round(1),
        "booked_revenue": g["booked_revenue"].sum().round(),
        "realised_revenue": g["realised_revenue"].sum().round(),
        "revenue_at_risk": g["revenue_at_risk"].sum().round(),
    })
    t["realised_per_booking"] = (g["realised_revenue"].sum() / g.size()).round(1)
    return t.sort_values("realised_per_booking", ascending=False)


channels = channel_table(clean)
print(channels.to_string())
channels.to_csv(OUT / "04_channel_quality_pandas.csv")

# Compare with the file exported from MySQL.
sql_q1a = pd.read_csv(SQL_DIR / "03_q1a_channel_quality.csv").set_index("market_segment")
diff = (channels[["bookings", "cancel_pct", "realised_per_booking"]]
        - sql_q1a.loc[channels.index, ["bookings", "cancel_pct", "realised_per_booking"]]).abs()
if (diff["bookings"] == 0).all() and (diff[["cancel_pct", "realised_per_booking"]] <= 0.11).all().all():
    print("\nMATCH: pandas and SQL give the same channel table.")
else:
    print("\nDIFFERENT: check these rows against your SQL result:")
    print(diff.to_string())

# ---------------------------------------------------------------------------
# 3. Lead-time bands with pd.cut (same bands as Query 2)
# ---------------------------------------------------------------------------
heading("3. Lead-time bands (Query 2)")

bins = [-1, 7, 30, 90, 180, np.inf]  # upper edges are included: 0-7, 8-30, ...
labels = ["1: 0-7 days", "2: 8-30 days", "3: 31-90 days", "4: 91-180 days", "5: 181+ days"]
clean["lead_band"] = pd.cut(clean["lead_time"], bins=bins, labels=labels)

by_band = (clean.groupby(["market_segment", "lead_band"], observed=True)
           .agg(bookings=("is_canceled", "size"),
                cancel_pct=("is_canceled", lambda s: round(s.mean() * 100, 1)))
           .reset_index())
by_band.to_csv(OUT / "04_channel_by_lead_time_pandas.csv", index=False)

sql_q2 = pd.read_csv(SQL_DIR / "03_q2_channel_by_lead_time.csv")
merged = by_band.merge(sql_q2, on=["market_segment", "lead_band"], suffixes=("_pd", "_sql"))
same = (len(merged) == len(by_band) == len(sql_q2)
        and (merged["bookings_pd"] == merged["bookings_sql"]).all()
        and ((merged["cancel_pct_pd"] - merged["cancel_pct_sql"]).abs() <= 0.11).all())
print("MATCH with Query 2." if same else "DIFFERENT from Query 2: check the bands.")

# ---------------------------------------------------------------------------
# 4. Same channel table with identical rows removed (Query 1c)
# ---------------------------------------------------------------------------
heading("4. Channel table without identical rows (Query 1c)")

no_dups = df[(~is_copy) & (df["adr"] > 0)]
channels_dedup = channel_table(no_dups)
print(channels_dedup[["bookings", "cancel_pct", "realised_per_booking"]].to_string())
channels_dedup.to_csv(OUT / "04_channel_quality_pandas_dedup.csv")

# ---------------------------------------------------------------------------
# 5. Simple risk grouping (no machine learning needed)
# ---------------------------------------------------------------------------
heading("5. Risk grouping: lead-time band x deposit type x channel")

MIN_BOOKINGS = 200       # my cut-off: smaller groups are too noisy to trust
HIGH_CANCEL_PCT = 50.0   # my cut-off for "high cancellation"

groups = (clean.groupby(["lead_band", "deposit_type", "market_segment"], observed=True)
          .agg(bookings=("is_canceled", "size"),
               cancel_pct=("is_canceled", lambda s: round(s.mean() * 100, 1)),
               revenue_at_risk=("revenue_at_risk", "sum"))
          .reset_index())
groups["revenue_at_risk"] = groups["revenue_at_risk"].round()
groups = groups[groups["bookings"] >= MIN_BOOKINGS]
groups["high_risk"] = groups["cancel_pct"] >= HIGH_CANCEL_PCT
groups = groups.sort_values("revenue_at_risk", ascending=False)
groups.to_csv(OUT / "04_risk_groups.csv", index=False)

print(f"groups with at least {MIN_BOOKINGS} bookings: {len(groups)}")
print(f"flagged high risk (cancel rate >= {HIGH_CANCEL_PCT:.0f}%): {int(groups['high_risk'].sum())}")
print("\nTop 10 groups by revenue at risk:")
print(groups.head(10).to_string(index=False))

hr = groups[groups["high_risk"]]
print(f"\nHigh-risk groups together: {int(hr['bookings'].sum())} bookings, "
      f"{int(hr['revenue_at_risk'].sum())} revenue at risk "
      f"({hr['revenue_at_risk'].sum() / clean['revenue_at_risk'].sum() * 100:.0f}% of all revenue at risk)")

# ---------------------------------------------------------------------------
# 6. Two charts for the write-up and the LinkedIn slides
# ---------------------------------------------------------------------------
heading("6. Charts")
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib is not installed, so the charts were skipped.")
    print("Install it with: pip install matplotlib")
else:
    plt.rcParams.update({"font.size": 13})

    # Chart 1: revenue per booking by channel, with and without identical rows.
    # "Undefined" (2 bookings, no revenue) is left out so there is no empty bar.
    order = [c for c in channels.index if c != "Undefined"]
    x = np.arange(len(order))
    all_rows = channels.loc[order, "realised_per_booking"]
    no_copies = channels_dedup.reindex(order)["realised_per_booking"]
    fig, ax = plt.subplots(figsize=(11, 6))
    bars1 = ax.bar(x - 0.2, all_rows, 0.4, label="All rows", color="#4C72B0")
    bars2 = ax.bar(x + 0.2, no_copies, 0.4, label="Identical rows removed", color="#DD8452")
    ax.bar_label(bars1, fmt="%.0f", padding=3, fontsize=11)
    ax.bar_label(bars2, fmt="%.0f", padding=3, fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=25, ha="right")
    ax.set_ylabel("Realised revenue per booking")
    ax.set_title("Channel ranking changes when identical rows are removed")
    ax.set_ylim(0, max(all_rows.max(), no_copies.max()) * 1.12)
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "Excludes Undefined (2 bookings). Bookings with adr of 0 or less are excluded.",
             fontsize=9, color="gray")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "04_chart_channel_revenue.png", dpi=200)
    plt.close(fig)

    # Chart 2: cancellation rate by lead-time band for the three biggest channels.
    fig, ax = plt.subplots(figsize=(11, 6))
    colours = {"Direct": "#4C72B0", "Online TA": "#DD8452", "Offline TA/TO": "#55A868"}
    for seg, colour in colours.items():
        s = by_band[by_band["market_segment"] == seg]
        xs = s["lead_band"].astype(str).tolist()
        ys = s["cancel_pct"].tolist()
        ax.plot(xs, ys, marker="o", linewidth=2.5, color=colour, label=seg)
        # First and last points get a label. The first labels sit to the left of
        # the points, and the last to the right, so they do not overlap.
        ax.annotate(f"{ys[0]:.0f}%", (xs[0], ys[0]), textcoords="offset points",
                    xytext=(-12, 0), ha="right", va="center", fontsize=11, color=colour)
        ax.annotate(f"{ys[-1]:.0f}%", (xs[-1], ys[-1]), textcoords="offset points",
                    xytext=(12, 0), ha="left", va="center", fontsize=11, color=colour)
    ax.set_ylabel("Cancellation rate (%)")
    ax.set_xlabel("Lead time (days between booking and arrival)")
    ax.set_title("Cancellations rise with lead time, least for Direct")
    ax.set_ylim(0, 60)
    ax.set_xlim(-0.4, 4.4)  # room for the labels at both ends
    ax.legend(loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "04_chart_cancel_by_lead_time.png", dpi=200)
    plt.close(fig)
    print("Saved 2 charts to the results folder.")

print("\nDone. Copy everything above and send it to me.")
