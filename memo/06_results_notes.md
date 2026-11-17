# Results notes for step 4b (python/06_timing_and_adjusted.py)

Plain-sentence notes on each table. All figures are from the script's own output on the cleaned data (117,430 rows, daily rate above zero). Written so the script can be rerun and the numbers checked against this page.

## When are cancellations made? (06_timing_test_group.csv, 06_reach_by_message_day.csv)

The test group is Online TA bookings with no deposit made more than 90 days ahead: 20,673 bookings, 9,884 cancelled (47.8%). The date a booking was cancelled comes from the column reservation_status_date, which is the date the last status was set. For a cancelled booking I read it as the cancellation date. For 136 of the 9,884 the status is No-Show, dated at arrival.

Counting back from arrival, 5.6% of the cancellations are in the last 7 days, 4.3% in days 8 to 14, 7.2% in days 15 to 30, 11.4% in days 31 to 60, 10.9% in days 61 to 90, 41.7% in days 91 to 180 and 19.0% more than 180 days before arrival. The median is 107 days before arrival, and 83.4% are at least 30 days before arrival.

Counting from the day of booking, 9.5% are on the same day, 20.1% in days 1 to 7, 7.7% in days 8 to 14, 9.3% in days 15 to 30, 12.3% in days 31 to 60, 10.7% in days 61 to 90 and 30.5% after day 90. The median is 40 days after booking.

If a message went out 3 days after booking, 78.3% of the eventual cancellations would still be ahead. For day 7 it is 70.5%, day 14 62.8%, day 30 53.5% and day 60 41.2%.

## Online TA against Direct, like for like (06_like_for_like.csv, 06_online_ta_vs_direct_gap.csv)

Online TA cancels 36.9% of bookings and Direct 15.4%. If Online TA had Direct's mix of hotel and lead-time band, its rate would be 27.2%. If Direct had Online TA's mix, its rate would be 19.3%. With identical rows removed the figures are 35.6% and 14.8% actual, and 26.1% and 18.6% with the other channel's mix. So the mix explains part of the gap, and a gap of about 11 to 18 points remains, depending on which channel's mix is used.

Within a hotel and lead-time band (groups of 200 or more bookings in both channels), the gap between Online TA and Direct is under one point for bookings made 0 to 7 days ahead in both hotels. It grows with lead time: City Hotel 13.6, 17.5, 23.8 and 27.3 points; Resort Hotel 8.9, 20.9, 29.0 and 30.7 points for the next four bands.

## Channel table with intervals (06_channel_quality_with_intervals.csv)

Intervals are 95% Wilson intervals on the cancellation rate. Online TA is 36.5% to 37.3% and Direct 14.8% to 16.0%. Aviation (231 bookings) and Complementary (63 bookings) have intervals too wide to rely on, and the file flags them.

## Break-even and sample size (06_break_even.csv, 06_sample_size.csv)

The average booked revenue of a cancelled booking in the test group is 555.4. At an assumed cost of 1.00 per treated booking, a reminder breaks even at a drop of 0.18 percentage points before commission and 0.21 after an assumed 15% commission. The costs and commission rates are assumptions, not data.

At 80% power and a 5% significance level, detecting a drop from the 47.8% baseline needs 1,555 bookings per group for 5 points, 4,336 for 3 points, 9,770 for 2 points and 39,130 for 1 point. At about 795 bookings a month, that is roughly 4, 11, 25 and 98 months for both groups together. Detecting the 0.18 point break-even drop would need about 1.2 million bookings per group.

## What these results do not show

They do not show why guests cancel, or whether a message would change that. Early cancellations may include guests who cancel and rebook, which the file cannot show because it has no booking ID. The like-for-like comparison controls for hotel and lead time only, not for deposit type, country or previous cancellations.
