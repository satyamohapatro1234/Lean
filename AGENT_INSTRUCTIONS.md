# 🤖 Instructions for AI Agents Developing This Project

**If you are an AI agent (Cline, Claude, Cursor, Copilot, or any other) working on this codebase, read this file first.**

---

## What This Project Is

A production-grade algorithmic trading platform. Real money will eventually run on this. Every decision matters. Do not improvise on architecture — the architecture is documented and reasoned.

---

## Before Writing Any Code

1. **Read PLAN.md** — Find which phase you are in. Understand what the current phase delivers.
2. **Read CONTEXT.md** — This is the full project history. Every decision is explained. Every mistake that was made is recorded so you don't repeat it.
3. **Read DECISIONS.md** — The quick reference for every technology decision and why.
4. **Read the README in the relevant folder** — e.g., if building data pipeline, read `data-pipeline/README.md`.

---

## Current Status (as of March 2026)

**Phase 0 — In Progress**

What exists:
- Docker infrastructure definition (`docker-compose.yml`)
- SQLite schema for instrument master (`instrument-master/schema.sql`) — already seeded with lot sizes and SEBI changes
- Fee schedule config (`config/fee_schedules.json`) — versioned pre/post Oct 2024
- NSE holidays config (`config/nse_holidays.json`)
- Architecture and documentation in all folders

What needs to be BUILT (Phase 0 deliverables):
- `instrument-master/brokers/dhan_parser.py`
- `instrument-master/daily_refresher.py`
- `data-pipeline/bhavcopy_downloader.py`
- `data-pipeline/intraday_downloader.py`
- `data-pipeline/lean_writer.py`
- `symbol-mapper/universal_mapper.py`
- `strategies/spider-wave/main.py` (minimal first version)
- `strategies/spider-wave/fee_model.py`
- `run_backtest.py` (top-level LEAN wrapper)
- `monitor.py` (Streamlit Phase 0 dashboard)

---

## Hard Rules — Never Break These

### Data Format Rules
```python
# LEAN price format — ALWAYS multiply by 10000, convert to int
lean_price = int(raw_price * 10000)   # ₹94.00 → 940000

# LEAN timestamp format — milliseconds since midnight
lean_ts = int((time.hour * 3600 + time.minute * 60 + time.second) * 1000)

# NSE data path format (minute data)
path = f"/data/lean/equity/india/minute/{symbol.lower()}/{date:%Y%m%d}_trade.zip"

# UTC for all storage — LEAN converts to IST via market-hours-database.json
timestamp_utc = timestamp_ist.astimezone(timezone.utc)
```

### Never Do Per-Symbol API Loop for EOD Data
```python
# WRONG — crashes at symbol 40, never resumes
for symbol in all_2000_symbols:
    data = dhan.get_daily(symbol, from_date, to_date)  # WRONG
    
# RIGHT — one file = all symbols
bhav_url = f"https://archives.nseindia.com/content/historical/EQUITIES/{year}/{mon}/cm{dd}{MON}{year}bhav.csv.zip"
response = requests.get(bhav_url)  # ONE request = 2000+ stocks
```

### Never Put Tick Prices in React State
```typescript
// WRONG — causes 200 renders/second, UI freezes
websocket.onmessage = (tick) => {
    setPrice(tick.price)  // NEVER DO THIS for ticks
}

// RIGHT — direct DOM mutation, bypasses React entirely
websocket.onmessage = (tick) => {
    const el = document.getElementById(`price-${tick.symbol}`)
    if (el) el.textContent = tick.price.toFixed(2)  // DO THIS
}
```

### Never Use Fixed Lot Sizes or Hardcoded STT
```python
# WRONG — lot size changed Dec 2024
LOT_SIZE_NIFTY = 50  # WRONG after Dec 26, 2024

# RIGHT — date-aware lookup
def get_lot_size(symbol: str, trade_date: date) -> int:
    cursor.execute(
        "SELECT lot_size FROM lot_size_history WHERE symbol=? AND effective_from<=? AND (effective_to IS NULL OR effective_to>=?) ORDER BY effective_from DESC LIMIT 1",
        (symbol, trade_date, trade_date)
    )
    return cursor.fetchone()[0]

# WRONG — STT changed Oct 2024
OPTIONS_STT = 0.001  # This is only correct AFTER Oct 1, 2024!

# RIGHT — load from fee_schedules.json using trade date
fee_schedule = get_fee_schedule_for_date(trade_date)
stt = fee_schedule['options_stt_sell_pct']
```

### Never Make Options Symbol IDs Without Instrument Master
```python
# WRONG — constructing IDs from scratch, breaks across expiry dates
dhan_id = f"{underlying}_{strike}_{expiry}_{option_type}"  # WRONG

# RIGHT — look up from instrument master
instrument = db.execute(
    "SELECT dhan_security_id FROM instruments WHERE symbol=? AND strike_price=? AND expiry_date=? AND option_type=?",
    (underlying, strike, expiry_date, option_type)
).fetchone()
dhan_id = instrument['dhan_security_id']
```

---

## Error Recovery Patterns

### Download Job Failed
```python
# The job queue handles this automatically
# Status goes from 'pending' → 'failed' 
# On restart, failed jobs are retried with exponential backoff
# Maximum 4 retries per job, then marked 'skipped' for manual review
```

### Dhan Token Expired
```python
# Check brokers/dhan/client.py for DhanClient
# Token refresh should run at 6 AM via cron
# If token expires during market hours:
#   1. Attempt refresh via Playwright
#   2. If refresh fails: halt trading, send alert, log to regulatory_changes table
```

### LEAN Subprocess Hangs
```python
# engine_wrapper.py should have a timeout
# Default: 30 minutes for backtests, 5 minutes for live orders
# On timeout: kill subprocess, mark job as failed, alert developer
```

### QuestDB Connection Refused
```bash
# QuestDB must be running (docker compose up)
# Check: curl http://localhost:9000/health
# ILP port 9009 is for ingestion (Python questdb-client library)
# PostgreSQL port 8812 is for queries (psycopg2)
```

---

## Code Style and Patterns

### Python
- Type hints on all function signatures
- Docstrings on all public functions with parameter types and what they return
- SQLite connections: always use context managers (`with sqlite3.connect(...) as conn`)
- QuestDB: use the `questdb.ingress.Sender` class for ILP writes
- Async where it matters (HTTP downloads, WebSocket) — sync elsewhere
- Log at INFO level for normal operations, WARNING for retries, ERROR for failures

### TypeScript/React
- Strict TypeScript — no `any` types
- Functional components only
- Custom hooks for data fetching and WebSocket subscription
- Props interfaces defined explicitly
- Files named in PascalCase for components, camelCase for hooks and utilities

### Testing
- Test every data transformation that touches money (fee calculation, lot size lookup, price conversion)
- Test symbol mapper round-trips (broker ID → LEAN → broker ID)
- Test with edge dates (the day of SEBI changes, day before, day after)
- Integration tests run against real QuestDB and SQLite (not mocked)

---

## What the Developer Values

- **Correctness over speed.** Getting the fee model right matters more than getting it fast.
- **Explicitness over magic.** Code should be obvious about what it does.
- **Resumability.** Any job that can take more than 10 seconds must be resumable after crash.
- **Production grade.** This will run with real money. No shortcuts on error handling.
- **Open source friendly.** Apache 2.0 license. No paid dependencies in the core pipeline.

---

## Questions to Ask Before Writing Any Component

1. Is this in the current phase? If not, it can wait.
2. Does this touch money? If yes, add a test first.
3. Is there a LEAN built-in for this? (Check LEAN Python docs first)
4. Will this component receive live ticks? If yes, it must NOT use React state.
5. Is this a new dependency? If yes, check the license (must be MIT, Apache 2.0, or BSD).
6. Does this involve fee calculations? If yes, check which fee schedule is applicable by date.
7. Does this involve lot sizes? If yes, use the date-aware lookup from lot_size_history.

---

*This file is written for AI agents. Humans should read CONTEXT.md for the full story.*
