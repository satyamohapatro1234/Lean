# Instrument Master

Unified SQLite database mapping instrument identifiers across all brokers and LEAN.

## Problem Solved

Every broker uses different identifiers for the same instrument:
- Dhan: `49581` (security_id)
- Zerodha: `10742530` (instrument_token)
- Upstox: `NSE_FO|58442` (instrument_key)
- LEAN: `Symbol("NIFTY", SecurityType.Future, Market.India)`

The instrument master is the single source of truth that maps all of these to each other.

## Files

- `schema.sql` — SQLite schema with instruments table, lot_size_history, download_jobs, regulatory_changes
- `brokers/dhan_parser.py` — Download and parse Dhan instrument master CSV
- `daily_refresher.py` — 6 AM daily job to refresh all broker instrument masters

## Critical Data

**lot_size_history**: SEBI changed lot sizes December 2024:
- Nifty: 50 → 25 (effective Dec 26, 2024)
- BankNifty: 15 → 30 (effective Dec 24, 2024)

Using wrong lot size = wrong margin calculation in backtests.

## Usage

```bash
# Initialize database
python instrument-master/brokers/dhan_parser.py

# Query: get Dhan security_id for NIFTY
sqlite3 instrument-master/instruments.db \
  "SELECT dhan_security_id FROM instruments WHERE symbol='NIFTY' AND instrument_type='INDEX'"

# Query: get current lot size for NIFTY
sqlite3 instrument-master/instruments.db \
  "SELECT lot_size FROM lot_size_history WHERE symbol='NIFTY' AND effective_to IS NULL"
```
