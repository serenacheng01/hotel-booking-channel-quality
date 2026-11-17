# AI log

How I used an AI assistant (Claude) on this project, what I did myself, and what I checked.

## What the assistant did

- Suggested the project plan and the business question.
- Drafted the Python scripts, the SQL files, the results notes, the memo and this documentation.
- Explained tools and steps (MySQL, DBeaver, pandas, Tableau Public).

## What I did

- Chose the dataset, the tools and the order of the steps, and chose to use Tableau Public instead of Power BI for now.
- Ran every script and query myself on my own machine: loaded the data into MySQL, ran the cleaning and analysis SQL, exported each result, ran the pandas script, and built the dashboard in Tableau Public.
- Decided my own cut-offs (a minimum group size of 200 bookings, and a high-risk line at a 50% cancellation rate) and stated them as my choices.
- Checked that the pandas results matched the MySQL results exactly.
- Reviewed the memo and corrected the dashboard note.

## How results were checked

- Row count, column count and the known counts of odd rows are asserted in `python/checks.py`.
- The channel table and lead-time table were built twice, in MySQL and in pandas, and compared (`MATCH`).
- Each cleaning choice was tested by repeating the analysis without it (identical rows, zero-rate rows).
- The findings numbers in the README and memo come from my result files. The sample-size figures in the test design are calculations, so re-run them if you change the assumptions (80% power, 5% significance).

## Mistakes found and corrected

- The count of identical rows was first stated as 31,981; the correct figure from my MySQL output is 31,994 extra copies.
- A first draft said Non Refund bookings cancel 98 to 100% of the time. One group (Groups, 8 to 30 days) is 93.9%, so the memo and dashboard now say 94 to 100%.
- A first draft of the memo called one group "the largest single group" and had an unclear closing sentence in the test limits; both were rewritten.
- In one test of a query, integer division gave a percentage of 0.0; the query now multiplies by 100.0.

## Review after publishing a first version

I asked for a critique of the project as an experienced data engineer and analyst would give it. It found one error and several weaknesses, and I fixed what could be fixed:

- The memo said the file does not show when a booking was cancelled. That was wrong: `reservation_status_date` records it. The statement came from the assistant and I had not checked it against the data dictionary. The timing analysis now uses the column and changed the test design.
- The Online TA result is now compared with Direct at the same hotel and lead time, small channels are flagged, and the effect size in the test design is tied to the break-even instead of to the months available.
- The database checks and the nine exports are now scripts, tested against my own data and my hand exports.

## What AI cannot tell you here

The assistant cannot say why guests cancelled, what a reminder would do, or what the hotels' costs and commissions are. Those need the business and a real test.
