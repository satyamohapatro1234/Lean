# GitHub Copilot Instructions — Global

You are working on a production algorithmic trading platform. Read `AGENTS.md`, `CONTEXT.md`, and `DECISIONS.md` at the start of every session.

## Non-Negotiable Coding Rules

### Data format (LEAN engine)
- Prices: `int(raw_price * 10000)` — ₹94.00 → 940000. Never use float prices in LEAN files.
- Timestamps: milliseconds since midnight. 9:15 AM = 33,300,000 ms. Not Unix timestamps.
- All timestamps stored as UTC. LEAN converts to IST via market-hours-database.json.

### Download architecture
- EOD stock data: Use NSE Bhavcopy (1 file = all stocks). Never per-symbol API loops.
- Intraday data: SQLite job queue (download_jobs table). Always resumable after crash.
- Rate limiting: Dhan historical API max 20 req/sec — use 8 req/sec with token bucket.

### Financial calculations
- Lot sizes: Query `lot_size_history` table with trade date. Never hardcode.
- STT/fees: Load from `config/fee_schedules.json` with trade date. Never hardcode.
- Order safety: Pre-margin check before any order. Human confirmation always required.

### Options
- Expiry dates: Always from instrument master SQLite. Never calculate from calendar.
- Post Nov 2024: Only Nifty50 (NSE) and Sensex (BSE) have weekly expiries.
- Post Dec 2024: Nifty lot size = 25 (was 50), BankNifty = 30 (was 15).

## Testing

Write tests for every function that touches money, data format, or fee calculations.
Run `pytest tests/ -v` before submitting any PR.
Key tests: `test_lean_format.py`, `test_fee_model.py`, `test_lot_sizes.py`, `test_symbol_mapper.py`.

## PR Requirements

Every PR must include:
1. What was built (bullet list)
2. Tests written and their results
3. How to verify the acceptance criteria from the issue
