# 🌍 Global AI Trading Platform

> **The world's first open-source, AI-native, multi-broker global trading terminal built on QuantConnect LEAN**

[![Plan](https://img.shields.io/badge/Plan-v4.0-blue)](./PLAN.md)
[![Phase](https://img.shields.io/badge/Phase-0%20In%20Progress-yellow)](./PLAN.md)
[![Engine](https://img.shields.io/badge/Engine-QuantConnect%20LEAN-green)](https://github.com/QuantConnect/Lean)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](./LICENSE)

---

## What This Is

A production-grade algorithmic trading platform combining:

- **QuantConnect LEAN** — battle-tested backtesting + live trading engine
- **Narang's 4-Component Framework** — Alpha → Risk → Portfolio → Execution
- **Spider Wave MTF System** — multi-timeframe wave strategy for NSE
- **9 AI Agents** — LangGraph + Claude API for analysis, optimization, and execution
- **Professional React Terminal** — KLineChart Pro, AG Grid, real-time WebSocket
- **Multi-Broker** — Dhan (first), then Zerodha, Upstox, Angel One, Fyers, Interactive Brokers

**First broker: Dhan** — provides historical options OHLCV + Open Interest data, rare among Indian brokers.

---

## Development Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0 | 🟡 In Progress | Foundation: instrument master, symbol mapper, data pipeline, first backtest |
| Phase 1 | ⬜ Planned | Strategy validation (Walk Forward + Monte Carlo + CPCV) |
| Phase 2 | ⬜ Planned | Dhan live integration + 2-week paper trading |
| Phase 3 | ⬜ Planned | FastAPI backend + 3 core agents + MCP server |
| Phase 4 | ⬜ Planned | Options intelligence + WaveSignal + StrategyAdvisor agents |
| Phase 5 | ⬜ Planned | More Indian brokers (Zerodha, Upstox, Angel One, Fyers) |
| Phase 6 | ⬜ Planned | Global markets (Interactive Brokers) |
| Phase 7 | ⬜ Planned | Full React trading terminal (11 sub-phases) |
| Phase 8 | ⬜ Planned | Open source launch + documentation + community |

---

## Architecture

```
LAYER 4 — FRONTEND (Phase 7)
  React + TypeScript + Next.js
  KLineChart Pro (Apache 2.0) · shadcn/ui · AG Grid · WebSocket

LAYER 3 — BACKEND API (Phase 3)
  FastAPI + WebSocket Manager
  LangGraph Agents (9 total) · MCP Server · Claude API

LAYER 2 — ENGINE (Phase 0–1)
  QuantConnect LEAN (Docker subprocess)
  Spider Wave Alpha · HRP Portfolio · VWAP Execution · Risk Guards
  Validation: IS → WFO → Monte Carlo → CPCV → OOS

LAYER 1 — DATA (Phase 0)
  NSE Bhavcopy → QuestDB (1 file/day = all 2000+ stocks, free)
  Dhan Intraday API → SQLite job queue → QuestDB (resumable)
  Instrument Master → SQLite · SEBI regulatory monitor
```

---

## 9 AI Agents

| Agent | Phase | Function |
|-------|-------|----------|
| BacktestOrchestrator | 3 | Natural language → full backtest → report |
| RiskMonitor | 3 | Live drawdown monitor, auto-liquidate at 5% |
| OptimizerAgent | 3 | Parameter optimization + Monte Carlo validation |
| WaveSignal | 4 | Spider MTF wave → options structure recommendation |
| StrategyAdvisor | 4 | Market view → specific strategy + strike selection |
| NewsAnalyst | 5 | NSE announcements → portfolio impact summary |
| OrderAssist | 5 | Natural language → verified order execution |
| MarketScan | 5 | F&O universe scan for unusual OI/IV buildup |
| PortfolioCoach | 5 | Portfolio health + rebalancing suggestions |

---

## Key Technology Decisions

| Component | Choice | Reason |
|-----------|--------|--------|
| Backtesting engine | QuantConnect LEAN | 10+ years production, India + global built-in |
| EOD data source | NSE Bhavcopy | Free, 1 file = ALL 2000+ stocks (not per-symbol API) |
| Tick database | QuestDB | 1.4M rows/sec, built for financial tick data, Apache 2.0 |
| Frontend chart | KLineChart Pro | Apache 2.0, drawing tools, no license restrictions |
| Python indicators | TA-Lib | C core, BSD license, 150+ indicators + 60 candlestick patterns |
| Portfolio model | HRP (Risk Parity) | López de Prado: beats Markowitz out-of-sample |
| Execution model | VWAP | Johnson (DMA): minimises market impact |
| Validation | IS+WFO+MC+CPCV+OOS | Davey + López de Prado combined |
| Fee model | Versioned by date | SEBI changed STT Oct 2024, lot sizes Dec 2024 |
| State management | Zustand + Direct DOM | Hot tick data uses DOM mutation, not React renders |

---

## Built From 12 Books

Every architecture decision traces to a specific book:

| Book | Author | Key Decision |
|------|--------|-------------|
| Inside the Black Box (2024) | Narang | Entire 4-component framework |
| Algorithmic Trading & DMA (2010) | Johnson | VWAP execution, fee model |
| Building Winning Algo Trading Systems (2014) | Davey | 5-gate validation, Monte Carlo |
| ML for Algorithmic Trading (2020) | Jansen | Data pipeline, corporate actions |
| Advances in Financial ML (2018) | López de Prado | CPCV, HRP portfolio |
| Systematic Trading (2015) | Carver | Forecast scaling, position sizing |
| Advanced Futures Trading Strategies (2023) | Carver | 30 tested strategies |
| ML for Asset Managers (2020) | López de Prado | HRP confirmed |
| Causal Factor Investing (2023) | López de Prado | Causal alpha design |
| Trading and Exchanges (2002) | Harris | Order type design |
| Leveraged Trading (2019) | Carver | Safe leverage calculation |
| Professional Automated Trading (2013) | Durenard | OMS lifecycle |

See [docs/BOOKS_REFERENCE.md](./docs/BOOKS_REFERENCE.md) for full details and links.

---

## Repository Structure

```
├── PLAN.md                        ← Master development plan (v4.0) — READ THIS FIRST
├── docker-compose.yml             ← One-command startup: LEAN + QuestDB + Redis
├── config/
│   ├── nse_holidays.json          ← NSE trading calendar (for bdate_range)
│   └── fee_schedules.json         ← Versioned STT/brokerage rates by date
├── instrument-master/
│   ├── schema.sql                 ← SQLite schema for unified instrument master
│   ├── brokers/
│   │   └── dhan_parser.py         ← Parse Dhan CSV instrument master
│   └── daily_refresher.py        ← 6 AM daily refresh (listings, lot sizes)
├── data-pipeline/
│   ├── bhavcopy_downloader.py     ← NSE Bhavcopy EOD (1 request = all stocks)
│   ├── intraday_downloader.py     ← Dhan intraday (SQLite job queue, resumable)
│   ├── lean_writer.py             ← QuestDB → LEAN binary zip format
│   ├── daily_updater.py           ← 16:30 IST daily update cron job
│   └── sebi_monitor.py            ← SEBI circular change detector + alerter
├── symbol-mapper/
│   └── universal_mapper.py        ← Dhan security_id ↔ LEAN Symbol mapping
├── strategies/
│   └── spider-wave/
│       ├── alpha_model.py         ← Spider MTF signals → LEAN Insights
│       ├── fee_model.py           ← DhanFeeModel (versioned STT)
│       └── main.py                ← Full LEAN algorithm (4 components)
├── brokers/
│   ├── dhan/                      ← Dhan WebSocket + REST (Phase 0–2)
│   ├── zerodha/                   ← Zerodha KiteConnect (Phase 5)
│   ├── upstox/                    ← Upstox API (Phase 5)
│   ├── angelone/                  ← Angel One SmartAPI (Phase 5)
│   ├── fyers/                     ← Fyers API (Phase 5)
│   └── interactive-brokers/       ← IB TWS via ib_insync (Phase 6)
├── agents/                        ← LangGraph AI agents (Phase 3+)
├── api/                           ← FastAPI backend (Phase 3)
├── frontend/                      ← React trading terminal (Phase 7)
│   ├── components/                ← Reusable UI components
│   ├── hooks/                     ← Custom React hooks
│   └── pages/                     ← Next.js pages
├── tests/                         ← Unit + integration tests
└── docs/
    ├── DATA_PIPELINE_COMPLETE.md  ← Complete data architecture (rate limits, bhavcopy)
    ├── CHARTING_RESEARCH.md       ← Charting library decision (why KLineChart)
    ├── DATABASE_RESEARCH.md       ← QuestDB selection vs TimescaleDB vs ClickHouse
    ├── BOOKS_REFERENCE.md         ← All 12 books with links + what each changed
    └── ALGOLOOP_ANALYSIS.md       ← AlgoLoop C# pattern analysis
```

---

## Data Pipeline — The Right Way

**The mistake most traders make:** Looping over 2000+ symbols making one API call per symbol. This fails at stock 40, has no retry, no resume, and takes hours.

**The correct approach:**

```
EOD data (free, all stocks at once):
  NSE Bhavcopy → 1 ZIP per day → all 2000+ stocks → 7 minutes for 10 years

Intraday data (rate-limited, resumable):
  SQLite job queue → 4,000 jobs → 8 req/sec → resumes after any crash

Live data:
  Broker WebSocket → Redis pub/sub → FastAPI WebSocket → Frontend
```

**Dhan rate limits:**
- Historical: 20 req/sec (we use 8 safely)
- Option chain: 1 req per 3 seconds
- Order placement: 25 orders/sec

**SEBI changes tracked automatically** (hash-diff monitor on NSE circulars):
- Oct 1, 2024: STT increased on F&O (options 0.0625% → 0.1%)
- Nov 20, 2024: Weekly expiries reduced to one per exchange
- Dec 24–26, 2024: New lot sizes (Nifty 50→25, BankNifty 15→30)
- Feb 10, 2025: No calendar spread margin benefit on expiry day

---

## Frontend Architecture

The critical insight for trading terminal frontends:

> Putting live tick prices into React state causes 200 re-renders/second. The UI becomes unusable. Hot data (ticks) must use direct DOM mutation. Only slow/medium data uses React state.

**Data speed tiers:**
- **Hot** (ticks, 100–200/sec): Direct DOM mutation via singleton WebSocket manager
- **Medium** (positions, P&L): Zustand + 5-second polling
- **Cold** (settings, config): Normal React state

Sub-phases for Phase 7 frontend:
1. Design system (Tailwind, shadcn, Storybook)
2. Layout shell (3-panel trading terminal)
3. Performance architecture (hot/medium/cold data flows)
4. Watchlist (direct DOM mutation, CSS flash)
5. KLineChart Pro (historical REST + streaming WebSocket)
6. Order entry panel (margin check → confirmation → execute)
7. Positions + orders (AG Grid Community, MIT)
8. Backtest results viewer (Recharts equity curve)
9. Options chain (D3.js IV heatmap + payoff graph)
10. AI assistant panel (LangGraph agent chat)
11. Settings + configuration

---

## Phase 0 Start Sequence (5 Days)

```bash
# Day 1: Infrastructure
docker compose up -d  # LEAN + QuestDB + Redis all running

# Day 2: Instrument master
python instrument-master/brokers/dhan_parser.py
# → SQLite DB loaded with Dhan symbol map

# Day 3: EOD data
python data-pipeline/bhavcopy_downloader.py --from 2014-01-01 --to 2024-12-31
# → QuestDB: ~10 years × 2000+ stocks = ~5M rows

# Day 4: Symbol mapping
python symbol-mapper/universal_mapper.py --test
# → NIFTY → Dhan security_id → LEAN Symbol → back to Dhan → passes round-trip

# Day 5: First backtest
python run_backtest.py
# → Equity curve JSON, Sharpe, max drawdown, trade list
```

---

*Plan v4.0 · Built from 12 books · Designed for production · Open for community*
