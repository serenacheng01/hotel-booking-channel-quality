# Hotel bookings: channel quality memo and test design

Serena · November 2026

## Decision and recommendation

Protect Online TA bookings first. Online TA holds 61% of all revenue at risk from cancellations (10.2 million of 16.7 million) on 48% of bookings, and its cancellation rate climbs from 10% for bookings made 0 to 7 days ahead to 54% at 181 or more days. Part of that is size and mix, but not all of it: if Online TA had Direct's mix of hotel and lead time it would still cancel 27.2% of bookings, against 15.4% for Direct.

Online TA is the channel with the most to protect, not necessarily the most profitable one. Under an assumed 10% commission its realised revenue per booking falls from 244.4 to 220.0, below Offline TA/TO (236.9). The commission rates are my assumption, so the recommendation holds only if protecting a booking is worth its revenue less commission.

I recommend testing an early-confirmation reminder on Online TA bookings with no deposit that were made 91 or more days ahead. That group is 20,673 bookings with 5.5 million of revenue at risk. In my risk grouping only the 181 or more day band meets the 50% line (53.5%); the 91 to 180 day band is 44.6% but holds the most revenue at risk (3.2 million), so the test group covers both bands.

The history shows who is likely to cancel, not that a reminder would stop it, so the next step is a randomised test, designed below. It also shows when: cancellations in this group are early. The median is 107 days before arrival and 40 days after booking, 83% happen at least 30 days before arrival, and 30% within a week of booking. A reminder sent shortly before arrival would reach about 10% of them, so the messages have to start in the first weeks after booking.

One ranking is not safe to quote: Offline TA/TO and Groups change sharply once identical rows are removed. The Online TA result does not (cancellation 36.9% with all rows, 35.6% without).

## Evidence

Direct earns the most per booking and cancels the least of the large channels, while Online TA is the biggest source of lost revenue. Revenue is booked rate times nights, and realised revenue counts only bookings that were not cancelled. The data does not state a currency.

| Channel | Bookings | Cancelled (%) | Realised revenue per booking | Revenue at risk | Realised per booking, identical rows removed |
| --- | --- | --- | --- | --- | --- |
| Direct | 12,366 | 15.4 | 331.5 | 993,410 | 339.2 |
| Aviation (too small to rely on) | 231 | 22.1 | 306.8 | 16,578 | 310.7 |
| Online TA | 56,110 | 36.9 | 244.4 | 10,227,646 | 253.1 |
| Offline TA/TO | 23,887 | 34.6 | 236.9 | 2,492,358 | 337.2 |
| Corporate | 5,213 | 18.9 | 110.9 | 196,383 | 116.9 |
| Groups | 19,558 | 61.7 | 95.6 | 2,800,544 | 195.5 |
| Complementary (too small to rely on) | 63 | 7.9 | 76.4 | 270 | 77.5 |

The two channels with fewer than 1,000 bookings are shown for completeness only; their cancellation rates have wide intervals (Aviation 17.2% to 27.9%, Complementary 3.4% to 17.3%). The larger channels have intervals of about two points or less (results/06_channel_quality_with_intervals.csv).

Cancellations rise with lead time in every large channel. For Online TA the rate goes from 9.6% at 0 to 7 days to 53.6% at 181 or more days, while Direct stays between 8.0% and 25.4%. The lead-time chart is on the dashboard.

Online TA also cancels more than Direct when they are compared like for like. For bookings made 0 to 7 days ahead the gap is under one point in both hotels. It then widens with lead time, to 27.3 points at the City Hotel and 30.7 at the Resort Hotel for bookings made 181 or more days ahead (groups of 200 or more bookings in both channels). With identical rows removed, Online TA with Direct's mix is 26.1% against Direct's 14.8%, so this result does not depend on that choice. Deposit type, country and previous cancellations are not controlled for.

The ranking also depends on the hotel. Offline TA/TO earns 421.0 per booking at the Resort Hotel but 154.7 at the City Hotel, so a single channel table mixes channel and hotel. Within a hotel and lead-time band, Direct ranks first everywhere except bookings made 0 to 7 days ahead, where Online TA is first in both hotels.

Bookings with no deposit hold the revenue at risk that a reminder could reach. For those, Online TA bookings made 91 or more days ahead (two lead-time bands, 13,203 and 7,470 bookings) hold 5.5 million at risk, which is 33% of all revenue at risk.

## Data decisions and checks

Six decisions shape the numbers, and each was tested instead of assumed. The raw table was never edited: a backup copy sits beside it, and the measures live in one SQL view that SQL, pandas and the dashboard all read.

| Decision | What I did | Effect on the result |
| --- | --- | --- |
| Identical rows (31,994 extra copies) | Kept them in the main results and repeated the analysis without them. The file has no booking ID, so I cannot tell copies from real bookings that look the same. | Groups cancellation falls from 61.7% to 27.9%. Offline TA/TO realised revenue per booking rises from 236.9 to 337.2. Online TA barely moves (36.9% to 35.6%). |
| Zero or negative daily rate (1,960 rows) | Removed them from the main results and repeated the channel table with them kept. | 680 of the 1,960 are Complementary bookings, 91.5% of that channel. The order of the other channels does not change, and each moves by less than 7 per booking. |
| Non Refund deposits | Left them out of the risk chart and the test group. | These bookings cancel 94 to 100% of the time in every group of 200 or more bookings, which looks like a labelling problem, not a real pattern. |
| Cancelled bookings earn nothing | Realised revenue is zero for a cancelled booking. | Assumes the room is not resold and no fee is kept. The data has neither. |
| Group size and high-risk cut-offs | Only groups with at least 200 bookings; high risk means a cancellation rate of 50% or more. | Both are my own choices, not data-driven. |
| Missing values | Turned the text placeholders into real blanks. Missing: agent 16,340, company 112,593, country 488, children 4. | None of these columns is used in a revenue figure. |

Two independent checks agree. The channel table and the lead-time table rebuilt in pandas match the MySQL results exactly, and an automated script confirms the row count, the allowed channel names and the known counts of odd rows each time the data is reloaded.

## Limits

The data shows which bookings were cancelled, not why, and not what would have prevented it.

- **No costs or fees.** There is no commission, cancellation fee or resale information, so revenue at risk is a ceiling on what could be saved. Under an assumed 10% Online TA commission, its realised revenue per booking falls from 244.4 to 220.0, below Offline TA/TO (236.9). The commission rates are my assumption, not data.
- **Room revenue only.** Revenue is the daily rate times nights. It excludes meals, extras and costs, so it is not profit.
- **Two hotels, 2015 to 2017.** One city hotel and one resort hotel, with arrivals from July 2015 to August 2017. Booking behaviour today may differ.
- **Identical rows are unresolved.** The channel ranking for Offline TA/TO and Groups depends on a choice the data cannot settle.
- **Cancellation timing is inferred.** The column reservation_status_date is the date the last status was set, which I read as the cancellation date for cancelled bookings. For 136 of the 9,884 cancellations in the test group the status is No-Show, dated at arrival. The file has no booking ID, so a guest who cancels and rebooks cannot be seen, and some of the cancellations within a week of booking may be of that kind.
- **The Non Refund deposit label looks unreliable,** so those bookings are outside the analysis.

## Test design: an early-confirmation reminder

The test asks one question: does a reminder lower the cancellation rate of high-risk bookings enough to pay for itself? The history cannot answer that, so this is a design for a test on future bookings, not a result.

**Who.** Online TA bookings with no deposit, made 91 or more days ahead. In the existing data that is 20,673 bookings, of which 9,884 cancelled (47.8%), with 5.5 million of revenue at risk. With identical rows removed the group is 18,061 bookings and 46.4% cancel, so the conclusion does not hinge on that choice.

**How.** Split the group 50/50 at random, with the booking as the unit. The treatment group gets the standard confirmation plus two reminders that restate the details and show how to change dates: one about 3 days after booking and one about 30 days after booking. It does not hide the cancellation option. The control group gets the standard confirmation only. The timing comes from the data: 78% of this group's cancellations happen after day 3 and 53.5% after day 30, while only about 10% happen in the last two weeks before arrival. A message before arrival would be a separate arm in a later test, and the data cannot say which timing works best.

**Primary metric.** Share of bookings cancelled before arrival. Secondary: realised revenue per booking, and date changes, to see whether guests move bookings instead of cancelling them.

**How many bookings.** The baseline cancellation rate is 47.8%. At 80% power and a 5% significance level, detecting a drop that size needs:

| Smallest drop worth detecting | Bookings per group | Total | Months at the historical volume |
| --- | --- | --- | --- |
| 5 percentage points | 1,555 | 3,110 | about 4 |
| 3 percentage points | 4,336 | 8,672 | about 11 |
| 2 percentage points | 9,770 | 19,540 | about 25 |

The group averaged roughly 795 bookings a month across the 26 months in the file. A 5-point drop is testable within a season. Smaller effects need most of a year, so I would plan for the 5-point version first.

**Cost side.** A saved booking is worth the revenue it keeps, on average 555 for the cancelled bookings in this group (about 472 after an assumed 15% commission). The reminder has to save more than it costs across everyone who receives it:

```latex
\text{break-even drop} = \frac{\text{cost per message}}{\text{revenue kept per saved booking}}
```

As an illustration only, a cost of 1.00 per treated booking against 555 per saved booking breaks even at a drop of about 0.18 percentage points (0.21 after a 15% commission). The 1.00 is an assumed figure, not data, and revenue is not profit, so the true break-even is higher. The real cost has to come from the business.

The break-even and the sample size pull in different directions. Detecting a 0.18 point drop would need about 1.2 million bookings per group, far more than exists, so this test can only detect drops of about 3 to 5 points. A result of no clear effect would not show that the reminder fails to pay, only that any effect is smaller than the test can see. The smallest drop worth acting on is a business decision, to be agreed before the test, not chosen because it fits the months available.

**Limits of this design.** A reminder cannot recover bookings that were never going to stay, and an incentive in the message would add cost and change who cancels. A booking only counts as saved if the guest actually stays, so the test should also track stays, not only cancellations.

## How it would run

The reminder would be an automated email, with SMS as an option, sent from a CRM or email platform and triggered when a booking is created.

- **Data needed per booking:** booking ID, channel, deposit type, booking date, arrival date, guest email (and a phone number if SMS is used), and a random group field set to reminder or control. This dataset has no booking ID or contact details, so in real use they would come from the hotel's booking system.
- **Trigger and timing:** reminders about 3 and 30 days after the booking is created, chosen because most cancellations in this group happen early. The best timing is untested.
- **Random group:** assigned in the data when the booking is created, and the platform sends only to the reminder group. Some platforms have a built-in holdout (Customer.io does). The data-field method works in any tool.
- **Consent and contact:** the hotel needs permission to message the guest, and SMS needs its own consent (Mailchimp requires this separately from email). Online TA guests may only have a masked email address, which has to be checked first.
- **Measuring:** cancellations before arrival and stays, by group, taken from the booking system.

Sources: [Mailchimp: About SMS marketing](https://mailchimp.com/help/about-sms-marketing), [Customer.io: Holdout tests](https://docs.customer.io/messaging/send/workflows/holdout-test/).

## Next steps and questions for the business

- **Get the real costs.** The cost of sending a reminder and the commission rates by channel decide whether the test is worth running, and neither is in the data.
- **Settle the identical rows.** Ask the data owner whether the repeated rows are duplicates or real bookings. It changes the Offline TA/TO and Groups results.
- **Explain the Non Refund label.** A 94 to 100% cancellation rate suggests a recording or policy issue, and it should be understood before anyone uses that field.
- **Check for cancel and rebook.** Ask whether the booking system can link a cancelled booking to a new one by the same guest. Without that link, the early cancellations may be rebookings, which a reminder would not save.
- **Look at prior cancellers.** In the test group, 319 bookings come from guests with a previous cancellation, and 97% of them cancelled. That is a small but very strong signal, worth its own look before the test.
