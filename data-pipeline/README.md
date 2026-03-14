# Data Pipeline

Three-tier data architecture for getting market data into QuestDB and LEAN.

## The Right Way to Download NSE Data

### Tier 1: NSE Bhavcopy (EOD — FREE, all stocks at once)
One ZIP file per trading day = OHLCV for ALL 2000+ listed stocks.
- 10 years of data in ~7 minutes
- Zero rate limiting (static file download)
- URL: `https://archives.nseindia.com/content/historical/EQUITIES/{year}/{MON}/cm{DD}{MON}{year}bhav.csv.zip`

```bash
python bhavcopy_downloader.py --from 2014-01-01 --to 2024-12-31 --segment equity
python bhavcopy_downloader.py --from 2014-01-01 --to 2024-12-31 --segment fo
```

### Tier 2: Dhan Intraday API (per-symbol, rate-limited, resumable)
- Rate limit: 20 req/sec (we use 8 safely)
- Window: 90 days per request (we use 85)
- Resumable: SQLite job queue — crash at job 400, restart at 401

```bash
# Create all 4,000 jobs for F&O universe
python intraday_downloader.py --create-jobs --universe fo --from 2019-01-01

# Run download (safe, resumable, 8 req/sec)
python intraday_downloader.py --run
```

### Tier 3: Live WebSocket (real-time forward fill only)
Dhan WebSocket → QuestDB ILP → Redis pub/sub → Frontend

## Files

| File | Purpose |
|------|---------|
| `bhavcopy_downloader.py` | NSE Bhavcopy EOD download (async, cached, all stocks) |
| `intraday_downloader.py` | Dhan intraday with SQLite job queue + token bucket rate limiter |
| `lean_writer.py` | Convert QuestDB data → LEAN binary zip format |
| `daily_updater.py` | 16:30 IST cron job — runs bhavcopy + writes LEAN files |
| `sebi_monitor.py` | Daily hash-diff check of NSE circulars, alerts on fee/lot changes |

## SEBI Changes That Affect This Pipeline

| Date | Change | Impact |
|------|--------|--------|
| Oct 1, 2024 | STT increased on F&O | fee_schedules.json versioned by date |
| Nov 20, 2024 | Weekly expiries reduced | Option chain universe changed |
| Dec 24–26, 2024 | New lot sizes | lot_size_history table with date ranges |

## QuestDB Tables

```sql
-- Tick data (live + historical intraday)
CREATE TABLE ticks (timestamp TIMESTAMP, symbol SYMBOL, price DOUBLE, volume LONG, bid DOUBLE, ask DOUBLE, oi LONG) TIMESTAMP(timestamp) PARTITION BY DAY;

-- OHLCV bars (daily from Bhavcopy, minute from intraday)
CREATE TABLE ohlcv (timestamp TIMESTAMP, symbol SYMBOL, timeframe SYMBOL, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume LONG) TIMESTAMP(timestamp) PARTITION BY MONTH;

-- Option chain snapshots
CREATE TABLE option_chain (timestamp TIMESTAMP, underlying SYMBOL, strike DOUBLE, expiry TIMESTAMP, ce_price DOUBLE, pe_price DOUBLE, ce_oi LONG, pe_oi LONG, ce_iv DOUBLE, pe_iv DOUBLE) TIMESTAMP(timestamp) PARTITION BY DAY;
```
