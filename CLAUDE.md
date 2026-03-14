# Global AI Trading Platform — Claude Code Project Instructions

This file is automatically loaded by Claude Code at the start of every session.

## First-Time Setup

If this is your first session on this project:
1. Read `CONTEXT.md` (full project history — 15 min read, worth it)
2. Read `DECISIONS.md` (quick lookup for all decisions)
3. Read `AGENT_INSTRUCTIONS.md` (hard rules for coding)
4. Check current phase in `PLAN.md`

## Current Phase

**Phase 0 — In Progress**

What needs building right now:
- `instrument-master/brokers/dhan_parser.py`
- `instrument-master/daily_refresher.py`
- `data-pipeline/bhavcopy_downloader.py`
- `data-pipeline/intraday_downloader.py`
- `data-pipeline/lean_writer.py`
- `symbol-mapper/universal_mapper.py`
- `strategies/spider-wave/fee_model.py`
- `strategies/spider-wave/main.py` (minimal)
- `run_backtest.py`
- `monitor.py` (Streamlit dashboard)

## Available Specialist Agents

Use the Task tool to invoke these agents. Each has deep context for their domain:

| Agent | Invoke For |
|-------|-----------|
| `orchestrator` | Starting a new phase, breaking down complex tasks, unsure what to do next |
| `data-agent` | Any data pipeline, bhavcopy, intraday download, LEAN format, instrument master |
| `quant-agent` | LEAN engine, Spider Wave strategy, backtesting, validation, symbol mapper |
| `backend-agent` | FastAPI API, WebSocket, broker integrations, LangGraph agents |
| `frontend-agent` | React terminal, KLineChart, AG Grid (Phase 7 only) |
| `test-agent` | Writing or running tests, especially for fee model or data format |
| `devops-agent` | Docker, docker-compose, cron jobs, health checks |
| `reviewer-agent` | Any code that touches money, orders, or fee calculations |
| `context-guardian` | After phase completion, new decisions, or mistakes found |

## Sub-Agent Routing Rules

**Parallel dispatch** (ALL conditions must be met):
- 3+ independent tasks touching different files/folders
- No shared state between tasks
- Example: data-agent builds bhavcopy_downloader while test-agent writes test_schema.py

**Sequential dispatch** (enforce order when ANY applies):
- Task B needs output from Task A
- Tasks share the same files
- Example: instrument-master schema → dhan parser → symbol mapper (strict order)

## The 5 Most Critical Rules

1. **LEAN prices:** `int(price * 10000)` — NOT float, NOT other multiplier
2. **EOD data:** NSE Bhavcopy (1 file = all stocks) — NEVER per-symbol API loop
3. **Live tick prices:** Direct DOM mutation — NEVER React setState()
4. **Fee rates:** Date-aware from config/fee_schedules.json — NEVER hardcoded
5. **Lot sizes:** Date-aware from lot_size_history table — NEVER hardcoded constant

## Money Safety Rules

Before any code that involves orders or live trading:
1. Pre-margin check required
2. Human confirmation required
3. reviewer-agent must approve
4. Paper trading test must pass (2 weeks minimum)

## Project Repository

https://github.com/satyamohapatro1234/Lean

First broker: Dhan  
Database: QuestDB (port 9009 ILP, 8812 PG)  
Cache: Redis (port 6379)  
Start everything: `docker compose up -d`
