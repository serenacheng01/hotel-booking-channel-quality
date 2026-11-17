# Step 3 results notes: channel quality

All numbers come from the MySQL results exported by `03_channel_quality.sql`.
Measures: nights = weekend + week nights; booked revenue = adr x nights; realised revenue = booked revenue for bookings that were not cancelled, else 0; revenue at risk = booked minus realised. The data does not state a currency, so values are shown as plain revenue units. The main tables use the view `v_bookings_clean` (adr > 0, 117,430 of 119,390 rows) and keep identical rows. Query 1c repeats the main table without them.

## Q1a channel quality (`03_q1a_channel_quality.csv`)
Direct earns the most realised revenue per booking (331.5) with a 15.4% cancellation rate. Online TA is the largest channel (56,110 bookings) and earns 244.4 per booking at 36.9% cancelled. Groups earns 95.6 per booking because 61.7% of its bookings cancel. Online TA holds about 61% of all revenue at risk (10.2 million of 16.7 million), because it is both large and cancels often.

## Q1b by hotel (`03_q1b_channel_by_hotel.csv`)
The channel ranking depends on the hotel. Offline TA/TO earns 421.0 per booking at the Resort Hotel (15.3% cancelled) but only 154.7 at the City Hotel (43.3% cancelled). Direct and Online TA keep similar positions in both hotels.

## Q1c identical rows removed (`03_q1c_channel_quality_dedup.csv`)
Removing the 31,994 identical rows changes the ranking. Offline TA/TO rises from 236.9 to 337.2 per booking, almost level with Direct (339.2), and its cancellation rate falls from 34.6% to 14.9%. Groups falls from 19,558 to 4,721 bookings, its cancellation rate from 61.7% to 27.9%, and its revenue per booking doubles to 195.5. Online TA and Direct barely move. The data has no booking ID, so I cannot prove whether the copies are errors or real bookings, and I report both versions.

## Q2 by lead time (`03_q2_channel_by_lead_time.csv`)
Cancellation rises with lead time in every large channel. Online TA cancels 9.6% of bookings made 0-7 days ahead and 53.6% of bookings made 181 or more days ahead. Direct stays between 8.0% and 25.4% across all bands, so it is the least sensitive to lead time.

## Q3 monthly cancellation (`03_q3_monthly_cancellation.csv`)
The monthly cancellation rate moves between 21.2% (November 2015) and 46.2% (July 2015), with no clear upward or downward trend. April to June 2017 was higher (43.5% to 44.1%) than the same months in 2016. The data starts in July 2015 and ends in August 2017, so I do not read a trend into this table.

## Q4 ranking within hotel and lead-time band (`03_q4_ranking_within_groups.csv`)
Direct ranks first in every hotel and lead-time band except bookings made 0-7 days ahead. In that band Online TA ranks first in both hotels (230.8 against 203.1 at the City Hotel, 180.7 against 149.2 at the Resort Hotel). The overall ranking therefore mostly holds, with that one flip. Only groups with at least 200 bookings are shown, a cut-off I chose.

## Q5a and Q5b the adr > 0 filter (`03_q5a_rows_removed_by_filter.csv`, `03_q5b_channel_quality_no_filter.csv`)
The filter removes 1,960 rows. Of those, 680 are Complementary bookings, which is 91.5% of that channel (probably free rooms by design). Every other channel loses under 3%. Without the filter the order of the top six channels does not change and each moves by less than 7 per booking, so the conclusion holds. Only Complementary changes much (76.4 to 6.5).

## Q6 commission sensitivity (`03_q6_commission_sensitivity.csv`)
The commission rates (10%, 15%, 20%) are my assumption, not data. With 10% commission Online TA falls from 244.4 to 220.0 per booking, which is already below Offline TA/TO (236.9). At 20% it falls to 195.5.

## What these results do not show
These are room revenue figures only. There are no costs, no commission data and no cancellation fees, and the data does not tell us whether a cancelled room was resold. Revenue at risk is therefore a ceiling on what a retention action could save, not an expected saving.
