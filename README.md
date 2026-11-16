# Advisor Map

A single page that shows doctoral advisors and their programs, grouped by the places they are in.

- `index.html` is the whole page. It has no build step.
- `data/` holds one CSV file per tab: advisors, programs, schools, locations, country, reactions.

## Reading from a Google Sheet

The page reads the "Advisor Map data" Sheet named in `CONFIG.sheetId`. Edits there show on the page at the next reload. The CSV files are a backup copy and are not updated from the Sheet automatically.

All cells in the Sheet are formatted as plain text, so dates and amounts stay as typed. Keep it that way: Google's CSV export drops values in a column that mixes numbers and text.

To point the page at a different Sheet:

1. Create a Google Sheet with six tabs named Advisors, Programs, Schools, Locations, Country and Reactions, using the same column names as the CSV files.
2. Share it as "Anyone with the link can view".
3. Copy the long code from the Sheet's address (between `/d/` and `/edit`) into `CONFIG.sheetId` near the bottom of `index.html`.

While `sheetId` is blank, or if the Sheet cannot be read, the page uses the CSV files.

Funding and healthcare figures were collected from public pages on 2026-11-15 and 2026-11-16 and are unverified until a date is entered in the `funding_verified` or `health_verified` column.
