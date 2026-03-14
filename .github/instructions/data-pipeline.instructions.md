---
applyTo: "data-pipeline/**,instrument-master/**"
---

# Data Pipeline Instructions

You are working in the data pipeline layer of this trading platform.

**The single most important rule in this folder:**
NSE EOD data MUST come from Bhavcopy (one ZIP per day = all 2000+ stocks).
Never write a loop that calls the broker API once per symbol for EOD data.
That is the bug that caused months of failures. Bhavcopy URL:
`https://archives.nseindia.com/content/historical/EQUITIES/{YEAR}/{MON}/cm{DD}{MON}{YEAR}bhav.csv.zip`

For intraday (per-symbol, rate-limited): use the SQLite job queue in `download_jobs` table.
Every job has a status (pending/completed/failed). The downloader reads only pending jobs.
Crashing and restarting continues from where it stopped — never from scratch.

QuestDB ports: 9009 for ILP ingestion (use `questdb.ingress.Sender`), 8812 for SQL (use psycopg2).

LEAN price format: `int(price * 10000)`. Timestamps: milliseconds since midnight.
