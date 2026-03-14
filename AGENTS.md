# Global AI Trading Platform — Agent Instructions

This file is read automatically by GitHub Copilot Coding Agent, Claude Code, and OpenAI Codex when they work on this repository.

## What This Project Is

A production-grade algorithmic trading platform on QuantConnect LEAN for NSE (Indian markets) and global markets. Real money will run on this. Every decision matters.

## Mandatory Reading Before Any Code

Before writing any code, read these files in this order:
1. `CONTEXT.md` — full project history, all decisions, all mistakes made
2. `DECISIONS.md` — quick lookup for every technology decision
3. `PLAN.md` — current phase and what needs to be built

## Current Phase: Phase 0

**What needs building right now:**
- `instrument-master/brokers/dhan_parser.py`
- `instrument-master/daily_refresher.py`
- `data-pipeline/bhavcopy_downloader.py`
- `data-pipeline/intraday_downloader.py`
- `data-pipeline/lean_writer.py`
- `symbol-mapper/universal_mapper.py`
- `strategies/spider-wave/fee_model.py`
- `strategies/spider-wave/main.py`
- `run_backtest.py`
- `monitor.py` (Streamlit dashboard)

## The 5 Rules That Cannot Be Broken

```
1. LEAN prices: int(price * 10000)     — NOT float, NOT other multiplier
2. EOD data: NSE Bhavcopy (1 URL = all 2000+ stocks) — NEVER loop over symbols
3. Lot sizes: date-aware lookup (lot_size_history table) — NEVER hardcoded
4. Fee rates: date-aware (config/fee_schedules.json) — NEVER hardcoded STT
5. Orders: always require pre-margin check + human confirmation
```

## How to Work on This Repo (GitHub Workflow)

1. Read the issue you were assigned — it contains the exact task and acceptance criteria
2. Read `AGENTS.md` (this file) and the relevant agent instructions in `.github/agents/`
3. Read `CONTEXT.md` for full background
4. Make changes, run tests, verify the acceptance criteria
5. Open a PR — include test results in the PR description
6. Request review from @satyamohapatro1234

## Project Infrastructure

```bash
# Start everything (required before any code runs)
docker compose up -d

# Services:
# QuestDB: localhost:9000 (web), 9009 (ILP ingestion), 8812 (SQL queries)
# Redis:   localhost:6379
# LEAN:    runs via subprocess (not as daemon)

# Run tests
pytest tests/ -v

# First backtest
python run_backtest.py
```

## Do Not Change Without Issue Approval

- Architecture decisions in `DECISIONS.md`
- `PLAN.md` phase structure
- `instrument-master/schema.sql` (ask first — seed data is production data)
- `config/fee_schedules.json` (SEBI fee rates — must be accurate)
- `docker-compose.yml` infrastructure
