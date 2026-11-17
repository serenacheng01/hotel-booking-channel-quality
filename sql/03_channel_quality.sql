-- =============================================================================
-- 03_channel_quality.sql
-- Project: hotel-booking-channel-quality
-- Purpose: rank booking channels (market_segment) by realised revenue per
--          booking, with the cancellation rate beside it, then test whether
--          the ranking holds up.
-- Needs:   02_checks_and_cleaning.sql run first (view v_bookings_clean and
--          table bookings_dedup must exist).
--
-- Definitions (set once in v_bookings_clean, see file 02):
--   nights           = stays_in_weekend_nights + stays_in_week_nights
--   booked_revenue   = adr * nights, every booking
--   realised_revenue = booked_revenue if is_canceled = 0, else 0
--   revenue_at_risk  = booked_revenue - realised_revenue (money in cancelled bookings)
-- Assumption: a cancelled room earns nothing (not resold, no fee kept).
--   The data has no cancellation fees, so this is a stated assumption.
--
-- Run each query on its own with Cmd+Enter, then export the result:
--   right-click the result grid > Export data > CSV, save into the sql folder
--   as the file name given above each query.
-- =============================================================================

USE hotel_bookings;

-- -----------------------------------------------------------------------------
-- Query 1a. THE MAIN TABLE: channel quality, all hotels together.
-- Export as: 03_q1a_channel_quality.csv
-- realised_per_booking divides by ALL bookings in the channel (cancelled ones
-- count as zero), so a high cancellation rate lowers it. That is the point.
-- -----------------------------------------------------------------------------
SELECT market_segment,
       COUNT(*)                                          AS bookings,
       ROUND(AVG(is_canceled) * 100, 1)                  AS cancel_pct,
       ROUND(SUM(booked_revenue))                        AS booked_revenue,
       ROUND(SUM(realised_revenue))                      AS realised_revenue,
       ROUND(SUM(booked_revenue - realised_revenue))     AS revenue_at_risk,
       ROUND(SUM(realised_revenue) / COUNT(*), 1)        AS realised_per_booking
FROM v_bookings_clean
GROUP BY market_segment
ORDER BY realised_per_booking DESC;

-- -----------------------------------------------------------------------------
-- Query 1b. The same table split by hotel (City Hotel and Resort Hotel).
-- Export as: 03_q1b_channel_by_hotel.csv
-- -----------------------------------------------------------------------------
SELECT hotel,
       market_segment,
       COUNT(*)                                          AS bookings,
       ROUND(AVG(is_canceled) * 100, 1)                  AS cancel_pct,
       ROUND(SUM(realised_revenue))                      AS realised_revenue,
       ROUND(SUM(realised_revenue) / COUNT(*), 1)        AS realised_per_booking
FROM v_bookings_clean
GROUP BY hotel, market_segment
ORDER BY hotel, realised_per_booking DESC;

-- -----------------------------------------------------------------------------
-- Query 1c. ROBUSTNESS CHECK: the same table with the identical rows removed.
-- Export as: 03_q1c_channel_quality_dedup.csv
-- Compare with Query 1a. Groups and Offline TA/TO lose most rows to
-- de-duplication, so if the ranking changes here, report it as a finding.
-- The measures are written out again because the view reads from bookings,
-- not from bookings_dedup.
-- -----------------------------------------------------------------------------
SELECT market_segment,
       COUNT(*)                                          AS bookings,
       ROUND(AVG(is_canceled) * 100, 1)                  AS cancel_pct,
       ROUND(SUM(CASE WHEN is_canceled = 0
                      THEN adr * (stays_in_weekend_nights + stays_in_week_nights)
                      ELSE 0 END))                       AS realised_revenue,
       ROUND(SUM(CASE WHEN is_canceled = 0
                      THEN adr * (stays_in_weekend_nights + stays_in_week_nights)
                      ELSE 0 END) / COUNT(*), 1)         AS realised_per_booking
FROM bookings_dedup
WHERE adr > 0
GROUP BY market_segment
ORDER BY realised_per_booking DESC;

-- -----------------------------------------------------------------------------
-- Query 2. Does lead time change the picture inside each channel?
-- Export as: 03_q2_channel_by_lead_time.csv
-- lead_time = days between booking and arrival. Bands are fixed here so the
-- pandas notebook can use the same ones (pd.cut with the same edges).
-- -----------------------------------------------------------------------------
SELECT market_segment,
       CASE WHEN lead_time <= 7   THEN '1: 0-7 days'
            WHEN lead_time <= 30  THEN '2: 8-30 days'
            WHEN lead_time <= 90  THEN '3: 31-90 days'
            WHEN lead_time <= 180 THEN '4: 91-180 days'
            ELSE                       '5: 181+ days' END AS lead_band,
       COUNT(*)                                          AS bookings,
       ROUND(AVG(is_canceled) * 100, 1)                  AS cancel_pct,
       ROUND(SUM(realised_revenue) / COUNT(*), 1)        AS realised_per_booking
FROM v_bookings_clean
GROUP BY market_segment, lead_band
ORDER BY market_segment, lead_band;

-- -----------------------------------------------------------------------------
-- Query 3. Window function: cancellation rate month by month.
-- Export as: 03_q3_monthly_cancellation.csv
-- The CTE (WITH ... AS) first turns the month name into a number, so months
-- sort in calendar order. LAG() looks at the previous row, which is the
-- previous month, so we can show the change in percentage points.
-- The first month has no previous month, so its change is NULL (blank).
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT arrival_date_year AS yr,
           CASE arrival_date_month
                WHEN 'January'   THEN 1  WHEN 'February' THEN 2
                WHEN 'March'     THEN 3  WHEN 'April'    THEN 4
                WHEN 'May'       THEN 5  WHEN 'June'     THEN 6
                WHEN 'July'      THEN 7  WHEN 'August'   THEN 8
                WHEN 'September' THEN 9  WHEN 'October'  THEN 10
                WHEN 'November'  THEN 11 WHEN 'December' THEN 12 END AS mth,
           COUNT(*)                         AS bookings,
           AVG(is_canceled) * 100           AS cancel_pct
    FROM v_bookings_clean
    GROUP BY arrival_date_year, mth
)
SELECT yr,
       mth,
       bookings,
       ROUND(cancel_pct, 1)                                    AS cancel_pct,
       ROUND(cancel_pct - LAG(cancel_pct) OVER (ORDER BY yr, mth), 1) AS change_vs_prev_month
FROM monthly
ORDER BY yr, mth;

-- -----------------------------------------------------------------------------
-- Query 4. CONTROL FOR CONFOUNDERS: does the channel ranking hold inside
-- each hotel and lead-time band?
-- Export as: 03_q4_ranking_within_groups.csv
-- Channel mix is tangled up with hotel and lead time (Groups book far ahead,
-- for example), so a raw ranking can mislead. RANK() orders the channels
-- inside each hotel + band. Only groups with at least 200 bookings are kept,
-- because rates from tiny groups are noise. 200 is my own cut-off; say so
-- in the memo.
-- If a channel's rank changes from group to group, that is a finding.
-- -----------------------------------------------------------------------------
WITH grouped AS (
    SELECT hotel,
           CASE WHEN lead_time <= 7   THEN '1: 0-7 days'
                WHEN lead_time <= 30  THEN '2: 8-30 days'
                WHEN lead_time <= 90  THEN '3: 31-90 days'
                WHEN lead_time <= 180 THEN '4: 91-180 days'
                ELSE                       '5: 181+ days' END AS lead_band,
           market_segment,
           COUNT(*)                                       AS bookings,
           AVG(is_canceled) * 100                         AS cancel_pct,
           SUM(realised_revenue) / COUNT(*)               AS realised_per_booking
    FROM v_bookings_clean
    GROUP BY hotel, lead_band, market_segment
    HAVING COUNT(*) >= 200
)
SELECT hotel,
       lead_band,
       market_segment,
       bookings,
       ROUND(cancel_pct, 1)                               AS cancel_pct,
       ROUND(realised_per_booking, 1)                     AS realised_per_booking,
       RANK() OVER (PARTITION BY hotel, lead_band
                    ORDER BY realised_per_booking DESC)   AS rank_in_group
FROM grouped
ORDER BY hotel, lead_band, rank_in_group;

-- -----------------------------------------------------------------------------
-- Query 5a. What did the adr > 0 filter remove, and from which channels?
-- Export as: 03_q5a_rows_removed_by_filter.csv
-- Write the total in the decision log.
-- -----------------------------------------------------------------------------
SELECT market_segment,
       COUNT(*)                      AS all_rows,
       SUM(adr <= 0)                 AS removed_by_filter,
       ROUND(SUM(adr <= 0) * 100.0 / COUNT(*), 1) AS removed_pct
FROM bookings
GROUP BY market_segment
ORDER BY removed_by_filter DESC;

-- -----------------------------------------------------------------------------
-- Query 5b. The main table again WITHOUT the filter (zero rates kept).
-- Export as: 03_q5b_channel_quality_no_filter.csv
-- Compare with Query 1a. Complementary and Corporate rooms are often free, so
-- this is where the filter matters. If the ranking changes, say so.
-- -----------------------------------------------------------------------------
SELECT market_segment,
       COUNT(*)                                          AS bookings,
       ROUND(AVG(is_canceled) * 100, 1)                  AS cancel_pct,
       ROUND(SUM(CASE WHEN is_canceled = 0
                      THEN adr * (stays_in_weekend_nights + stays_in_week_nights)
                      ELSE 0 END) / COUNT(*), 1)         AS realised_per_booking
FROM bookings
GROUP BY market_segment
ORDER BY realised_per_booking DESC;

-- -----------------------------------------------------------------------------
-- Query 6. COMMISSION SENSITIVITY (an ASSUMPTION, not from the data).
-- Export as: 03_q6_commission_sensitivity.csv
-- The data has no commission figures. Online travel agents typically charge
-- a percentage of the booking, so Online TA revenue after commission is lower
-- than it looks. The three rates below (10%, 15%, 20%) are assumed
-- low / middle / high values for illustration. Replace them if you find a
-- sourced figure, and label the table "assumed" wherever you show it.
-- Only the Online TA segment is reduced. Other channels stay as they are.
-- -----------------------------------------------------------------------------
SELECT market_segment,
       ROUND(SUM(realised_revenue) / COUNT(*), 1)                  AS per_booking_no_commission,
       ROUND(SUM(realised_revenue) / COUNT(*)
             * CASE WHEN market_segment = 'Online TA' THEN 0.90 ELSE 1 END, 1) AS per_booking_if_10pct,
       ROUND(SUM(realised_revenue) / COUNT(*)
             * CASE WHEN market_segment = 'Online TA' THEN 0.85 ELSE 1 END, 1) AS per_booking_if_15pct,
       ROUND(SUM(realised_revenue) / COUNT(*)
             * CASE WHEN market_segment = 'Online TA' THEN 0.80 ELSE 1 END, 1) AS per_booking_if_20pct
FROM v_bookings_clean
GROUP BY market_segment
ORDER BY per_booking_no_commission DESC;
