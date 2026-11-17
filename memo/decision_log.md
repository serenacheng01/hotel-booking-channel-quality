# Decision log

Each choice that changes the numbers, why I made it, and what I did to test it. Figures come from my own MySQL and pandas outputs (`sql/03_q*.csv`, `results/04_*.csv`).

| # | Decision | Why | How I tested it | Effect |
| --- | --- | --- | --- | --- |
| 1 | Use `hotel_bookings.csv` from the paper's data (TidyTuesday copy: `hotels.csv`) | Public, documented, 119,390 bookings from two hotels, and has channel, lead time, rate and cancellation status | Row and column counts checked after load (`01_load.py`, `checks.py`) | 119,390 rows, 32 columns |
| 2 | Turn the text placeholders `NULL` and `NA` into real blanks when loading | Otherwise numeric columns load as text | Missing counts checked: agent 16,340, company 112,593, country 488, children 4 | None of these columns is used in a revenue figure |
| 3 | Never edit the raw table; keep a backup copy and define all measures once in the view `v_bookings_clean` | One definition for SQL, pandas and the dashboard | Pandas results compared with the SQL exports | Channel and lead-time tables match exactly |
| 4 | Revenue = daily rate (adr) x (weekend nights + week nights). Realised revenue counts only bookings that were not cancelled | The file has no total price | Definitions written as comments in `02_checks_and_cleaning.sql` | Room revenue only, currency not stated |
| 5 | Cancelled bookings earn zero | Simplest assumption; the data has no cancellation fees or resale | Stated as an assumption in the memo | Revenue at risk is a ceiling, not an expected saving |
| 6 | Remove rows with a daily rate of zero or below (1,960 rows) | A zero rate cannot be a revenue figure | Repeated the channel table without the filter (`03_q5b_channel_quality_no_filter.csv`) and listed what was removed (`03_q5a_rows_removed_by_filter.csv`) | 680 of 743 Complementary bookings (91.5%) are removed; the order of the other channels does not change, each moves by less than 7 per booking |
| 7 | Keep identical rows (31,994 extra copies) in the main results and repeat the analysis without them | The file has no booking ID, so copies cannot be told from real bookings that look the same | Dedup comparison (`03_q1c_channel_quality_dedup.csv`) | Groups cancellation 61.7% to 27.9%; Offline TA/TO realised per booking 236.9 to 337.2; Online TA 36.9% to 35.6%. Unresolved, listed as a question for the data owner |
| 8 | Lead-time bands 0-7, 8-30, 31-90, 91-180, 181+ days | Short-notice, month, quarter, half-year and long-range bookings | Same bands built in SQL (CASE) and pandas (`pd.cut`) and compared | Results match |
| 9 | Only compare groups with at least 200 bookings | Rates from small groups are noise | Applied in query 4 and in the pandas risk grouping | My own cut-off, not data-driven |
| 10 | High risk = cancellation rate of 50% or more | A simple, explainable line | Applied in `04_pandas_channel_analysis.py` (`HIGH_CANCEL_PCT`) | My own cut-off, not data-driven |
| 11 | Leave Non Refund deposits out of the risk chart and the test group | They cancel 94 to 100% of the time in every group of 200 or more bookings, which looks like a labelling problem | Checked every channel, hotel and lead-time group of 200 or more | Excluded; listed as a question for the business |
| 12 | Choose Tableau Public for the dashboard | Free, works on a Mac, publishes to the web | Built three charts and a caveats note | Workbook is public, so only aggregate results are shown |
| 13 | Use an assumed commission of 10%, 15% and 20% only as a labelled sensitivity | The data has no commissions | `03_q6_commission_sensitivity.csv` | Online TA realised per booking 244.4 falls to 220.0 / 207.8 / 195.5. Rates are assumptions, not data |
| 14 | Test group: Online TA, no deposit, made 91 or more days ahead | Largest block of revenue at risk that a reminder could plausibly reach | Counted from the cleaned view in MySQL | 20,673 bookings, 9,884 cancelled (47.8%), 5,489,115 at risk (33% of all); 18,061 bookings and 46.4% without identical rows |
| 15 | Treat the reminder test as a design, not a result | History shows who cancels, not that a reminder would stop it | Sample sizes computed for 5, 3 and 2 percentage-point drops (80% power, 5% significance) | 1,555, 4,336 and 9,771 bookings per group |

## Added after review

| # | Decision | Why | How I tested it | Effect |
| --- | --- | --- | --- | --- |
| 16 | Use `reservation_status_date` as the cancellation date | The first memo wrongly said the file does not show when a booking was cancelled; the column is the date the last status was set | Checked that no cancelled booking is dated after arrival or before booking (`06_timing_and_adjusted.py`) | Median cancellation 107 days before arrival and 40 days after booking; 83.4% at least 30 days before arrival. Reminder timing moved from "before arrival" to about 3 and 30 days after booking |
| 17 | Compare Online TA with Direct like for like | The 61% share is partly size and mix | Re-weighted each channel to the other's hotel and lead-band mix, with and without identical rows | Online TA with Direct's mix 27.2% against Direct's 15.4% (26.1% against 14.8% without identical rows) |
| 18 | Flag channels under 1,000 bookings as too small to rely on | Aviation (231) and Complementary (63) have wide intervals | Wilson 95% intervals (`06_channel_quality_with_intervals.csv`) | Both stay in the table but are not used in any conclusion |
| 19 | Treat the break-even as a business input, not a design input | At 1.00 per message the break-even is 0.18 points, which needs about 1.2 million bookings per group to detect | `06_break_even.csv`, `06_sample_size.csv` | The test can only detect drops of about 3 to 5 points; the minimum worth acting on is to be agreed with the business first |
| 20 | Move database checks and exports into scripts | Nine hand-made exports made the MATCH check depend on a manual step | `checks_db.py` and `run_sql_exports.py` reproduce the nine files from the SQL file | Differences from the hand exports: none, apart from a rounding of 1 in one revenue figure |

## Things I did not do

- I did not use the `reservation_status` columns as predictors, because they record the outcome (checked in step 10 of `00_profile.py`).
- I did not build a prediction model. The question was which channel to protect and what to test, and a model would not answer that without a test.
- I did not convert revenue to profit or a single currency.
