-- =============================================================================
-- 02_checks_and_cleaning.sql
-- Project: hotel-booking-channel-quality
-- Purpose: check the loaded data, keep an untouched backup, test the duplicate
--          rows, and define the revenue measures once in a view.
-- Database: hotel_bookings (MySQL). Table: bookings (loaded by python/01_load.py).
--
-- How to run in DBeaver:
--   Option+X runs the whole script (every statement, one result tab each).
--   Cmd+Enter runs only the statement your cursor is in.
-- Run it from the top. The backup and dedup tables are rebuilt each time.
-- =============================================================================

USE hotel_bookings;

-- -----------------------------------------------------------------------------
-- 1. Did every row arrive?
-- Expected: 119390 (the same as the CSV).
-- -----------------------------------------------------------------------------
SELECT COUNT(*) AS rows_in_table FROM bookings;

-- -----------------------------------------------------------------------------
-- 2. Column names and types, so every later query uses the exact names.
-- Keep this output (File > Export, or copy it) for your notes.
-- -----------------------------------------------------------------------------
DESCRIBE bookings;

-- -----------------------------------------------------------------------------
-- 3. Keep an untouched copy of the loaded data.
-- If a later cleaning step goes wrong, rebuild from bookings_raw.
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS bookings_raw;
CREATE TABLE bookings_raw AS SELECT * FROM bookings;

-- -----------------------------------------------------------------------------
-- 4. Were the text placeholders turned into real NULLs by the load script?
-- Expected: agent 16340, company 112593, country 488, children 4 missing.
-- Expected: text_null_agent = 0 (no placeholder words left).
-- -----------------------------------------------------------------------------
SELECT SUM(agent IS NULL)    AS missing_agent,
       SUM(company IS NULL)  AS missing_company,
       SUM(country IS NULL)  AS missing_country,
       SUM(children IS NULL) AS missing_children,
       SUM(agent = 'NULL')   AS text_null_agent
FROM bookings;

-- -----------------------------------------------------------------------------
-- 5. Odd rows (see Step 2a of the guide).
-- adr is the average daily rate. Zero or negative rates and zero-night stays
-- need a decision, and each decision goes in the decision log.
-- Expected: adr_zero 1959, adr_negative 1, zero_nights 715, zero_adults 403.
-- -----------------------------------------------------------------------------
SELECT SUM(adr = 0) AS adr_zero,
       SUM(adr < 0) AS adr_negative,
       MAX(adr)     AS highest_adr,
       SUM(stays_in_weekend_nights + stays_in_week_nights = 0) AS zero_nights,
       SUM(adults = 0) AS zero_adults
FROM bookings;

-- -----------------------------------------------------------------------------
-- 6. Exact duplicate rows.
-- The file has no booking ID, so a copy may be a mistake or a real booking
-- that looks identical. SELECT DISTINCT * keeps one of each different row.
-- Extra copies = all rows minus distinct rows. Expected: about 31994.
-- -----------------------------------------------------------------------------
SELECT (SELECT COUNT(*) FROM bookings)
     - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM bookings) AS d) AS extra_copies;

-- -----------------------------------------------------------------------------
-- 7. A deduplicated copy, used only as a check on the main results.
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS bookings_dedup;
CREATE TABLE bookings_dedup AS SELECT DISTINCT * FROM bookings;

-- -----------------------------------------------------------------------------
-- 8. Where are the duplicates? Compare channels with and without them.
-- A random copying error would hit every channel about equally. This does not.
-- Groups and Offline TA/TO lose the most rows, and their cancellation rates
-- fall sharply. Online TA and Direct barely change.
-- -----------------------------------------------------------------------------
SELECT 'all rows' AS version,
       market_segment,
       COUNT(*) AS bookings,
       ROUND(AVG(is_canceled) * 100, 1) AS cancel_pct
FROM bookings
GROUP BY market_segment
UNION ALL
SELECT 'deduplicated',
       market_segment,
       COUNT(*),
       ROUND(AVG(is_canceled) * 100, 1)
FROM bookings_dedup
GROUP BY market_segment
ORDER BY market_segment, version;

-- -----------------------------------------------------------------------------
-- 9. The measures, defined once in a view.
-- Every later query, the pandas notebook and the dashboard use this definition.
--   nights           = weekend nights + week nights
--   booked_revenue   = adr * nights, for every booking
--   realised_revenue = the same, but 0 if the booking was cancelled
-- WHERE adr > 0 removes zero and negative rates. Report how many rows this drops.
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_bookings_clean;
CREATE VIEW v_bookings_clean AS
SELECT *,
       stays_in_weekend_nights + stays_in_week_nights AS nights,
       adr * (stays_in_weekend_nights + stays_in_week_nights) AS booked_revenue,
       CASE WHEN is_canceled = 0
            THEN adr * (stays_in_weekend_nights + stays_in_week_nights)
            ELSE 0 END AS realised_revenue
FROM bookings
WHERE adr > 0;

-- -----------------------------------------------------------------------------
-- 10. Check the view. Expected: 117430 rows (119390 minus 1960 with adr <= 0).
-- -----------------------------------------------------------------------------
SELECT COUNT(*) AS rows_in_view FROM v_bookings_clean;
