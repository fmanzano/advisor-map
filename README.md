# Advisor Map

A single page that shows doctoral advisors and their programs, grouped by the places they are in.

- `index.html` is the whole page. It has no build step.
- `data/` holds one CSV file per tab: advisors, programs, schools, locations, country, reactions.

## Reading from a Google Sheet

1. Create a Google Sheet with six tabs named Advisors, Programs, Schools, Locations, Country and Reactions, using the same column names as the CSV files.
2. Share it as "Anyone with the link can view".
3. Copy the long code from the Sheet's address (between `/d/` and `/edit`) into `CONFIG.sheetId` near the bottom of `index.html`.

While `sheetId` is blank, or if the Sheet cannot be read, the page uses the CSV files.

Funding and healthcare figures were collected from public pages on 2026-11-15 and are unverified until a date is entered in the `funding_verified` or `health_verified` column.
