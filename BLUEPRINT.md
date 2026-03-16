# 🌍 Global AI Trading Platform — Complete System Blueprint

**Version:** 1.0 — Fresh Start  
**Date:** 2026-03-16  
**Engine:** QuantConnect LEAN (git submodule at `engine/Lean/`)  
**Goal:** Open-source, AI-native, multi-market trading terminal — Indian + International markets  
**Status:** Pre-build — planning complete, code not yet written

---

## 📚 Book Library — Research Foundation

Every architectural decision below traces to a specific book. This is why those decisions were made.

### Trading Strategy & System Design
| Book | Author | Key Contribution to This Platform |
|------|--------|-----------------------------------|
| *Inside the Black Box* (2024) | Rishi Narang | 4-component framework: Alpha → Risk → Portfolio → Execution. No exceptions. |
| *Building Winning Algorithmic Trading Systems* (2014) | Kevin Davey | 5-gate validation: IS → WFO → Monte Carlo → CPCV → OOS. Paper trade before live. |
| *Algorithmic Trading and DMA* (2010) | Barry Johnson | VWAP execution, realistic fee modelling, slippage estimation. |
| *Machine Learning for Algorithmic Trading* (2020) | Stefan Jansen | Dollar bars, feature engineering, data pipeline, survivorship bias prevention. |
| *Advances in Financial ML* (2018) | Marcos López de Prado | CPCV, HRP portfolio construction, financial data stationarity. |
| *Systematic Trading* (2015) | Robert Carver | Forecast scaling (−20/+20), buffered rebalancing, IDM (Instrument Diversification Multiplier). |
| *Advanced Futures Trading Strategies* (2023) | Robert Carver | 30 tested strategies, regime-aware allocation, gradual capital transitions. |
| *ML for Asset Managers* (2020) | López de Prado | HRP confirmed outperforms Markowitz OOS. |
| *Causal Factor Investing* (2023) | López de Prado | Causal alpha design — correlation is not enough; understand the mechanism. |
| *Trading and Exchanges* (2002) | Larry Harris | Market microstructure, order types, thin-market execution risk. |
| *Leveraged Trading* (2019) | Robert Carver | Safe leverage formula: target_leverage = target_risk / instrument_vol. |
| *Professional Automated Trading* (2013) | Durenard | OMS lifecycle, priority queues, latency class separation. |

### System Design & Software Architecture
| Book | Author | Key Contribution |
|------|--------|-----------------|
| *Designing Data-Intensive Applications* | Martin Kleppmann | Event-driven architecture, stream processing, database internals for time-series. |
| *Clean Architecture* | Robert C. Martin | Dependency inversion, use-case driven layers, decoupled components. |
| *System Design Interview Vol 1 & 2* | Alex Xu | Distributed systems patterns, WebSocket scaling, real-time data flow architecture. |
| *Fundamentals of Software Architecture* | Richards & Ford | Architecture fitness functions, evolutionary design, component coupling. |

### Frontend & Real-Time Systems
| Book | Author | Key Contribution |
|------|--------|-----------------|
| *High Performance Browser Networking* | Ilya Grigorik | WebSocket protocol internals, delta updates, connection management. |
| Research: React WebSocket Best Practices (2025) | Various | Direct DOM mutation for hot data (not React state); memoization; virtualisation. |

### AI Agents & LLMs
| Book/Paper | Key Contribution |
|-----------|-----------------|
| TradingAgents (Tauric Research, 2026) | Multi-agent LLM framework; dual LLM (deep-think vs quick-think); LangGraph + Ollama. |
| LangGraph v1.0 (2025) | Graph-based stateful orchestration; A2A protocol support; human-in-the-loop built in. |

---

## ✅ Core Decisions — Locked

### What is LEAN and where does it live?
QuantConnect LEAN is an open-source C# backtesting and live trading engine. It is the **heart** of this platform.

**How it lives in this repo:** As a **git submodule** at `engine/Lean/`. This means:
- The repo tracks the exact LEAN commit we tested against
- Anyone who clones this repo runs `git submodule update --init --recursive` and gets the exact same LEAN version
- We can submit PRs to LEAN for Indian market bug fixes
- Our custom strategies, data pipeline, and broker integrations sit **alongside** LEAN, not inside it

**How LEAN runs:** Built from source via `dotnet build`. Executed as a subprocess:
```
engine/Lean/Launcher/bin/Release/QuantConnect.Lean.Launcher.exe --config=lean-config.json
```
**No Docker. No LEAN CLI.** The LEAN CLI only works via Docker, which is not installed.

**Python constraint:** LEAN's bundled pythonnet 2.0.53 requires **Python ≤ 3.11**. Create `.venv311` with Python 3.11 for all LEAN-touching code. Main `.venv` (3.14) for data pipeline and FastAPI.

### International Brokers — Free Data When You Have an Account
| Broker | What LEAN Already Has | Market | Data Free With Account |
|--------|----------------------|--------|----------------------|
| **Alpaca** | Official LEAN plugin | US Equities, Options, ETFs | ✅ Yes — 10 years 1-min historical + real-time IEX |
| **OANDA** | Official LEAN plugin | Forex, CFDs (70+ pairs) | ✅ Yes — tick data + historical since 2007 |
| **Interactive Brokers** | Official LEAN plugin | US, Global equities, futures, options, forex | ✅ Yes — delayed free, real-time with data subscription |
| **Tastytrade** | Official LEAN plugin | Options, futures | ✅ Yes — real-time with account |

### Indian Brokers — User Provides Their Own
| Broker | LEAN Status | Notes |
|--------|-------------|-------|
| **Dhan** | Custom (we build) | Best for options OI history, free data with 25 F&O trades/month |
| **Zerodha** | Official LEAN plugin | ZerodhaBrokerageModel built into LEAN core |
| **Samco** | Official LEAN plugin | SamcoBrokerageModel built into LEAN core |
| **Upstox** | Custom (we build) | Good API v2, popular with developers |
| **Angel One** | Custom (we build) | SmartAPI, well-documented |
| **Fyers** | Custom (we build) | Clean REST + WebSocket |

### Technology Stack — Final
| Component | Choice | Why |
|-----------|--------|-----|
| Backtesting engine | QuantConnect LEAN (git submodule) | 10+ years production, India + global built-in |
| Python strategy runtime | .venv311 (Python 3.11) | pythonnet 2.0.53 constraint |
| Tick database | QuestDB | 1.4M rows/sec, built for trading, Apache 2.0 |
| Pub/sub | Redis | Sub-ms pub/sub for live tick distribution |
| Backend API | FastAPI (Python 3.14) | Async, type-safe, fast |
| Task queue | Celery + Redis | Long-running backtests and downloads |
| Frontend | React + TypeScript + Next.js | Best ecosystem, Vercel deployment |
| Charts | KLineChart Pro (Apache 2.0) | Drawing tools, indicators, no restrictions |
| Data grids | AG Grid Community (MIT) | High-frequency row updates, virtualisation |
| State (hot) | Direct DOM mutation | WebSocket callbacks, NOT React state |
| State (medium) | Zustand + 5-sec polling | Positions, P&L |
| State (cold) | React state | Settings, config |
| AI framework | LangGraph v1.0 | Stateful, A2A-compatible, human-in-the-loop |
| AI online | Claude API (claude-sonnet-4-20250514) | Best reasoning for complex analysis |
| AI offline | Qwen via Ollama (RTX 3060) | Fallback when Claude unreachable |
| AI routing | LLMRouter class | Try Claude → if fail/timeout → Ollama |
| Protocol: tools | MCP | Connects agents to tools (LEAN, QuestDB, brokers) |
| Protocol: agents | A2A v1.0 | Async agents communicate via HTTP/JSON-RPC |
| Instrument master | SQLite | Symbol maps, lot sizes, fee schedules |
| EOD data | NSE Bhavcopy (India) + Alpaca historical (US) | 1 file/day for India, free API for US |
| Indicator library | TA-Lib (C core, BSD) | 150+ indicators, fast, stable |
| Portfolio model | HRP (RiskParityPortfolioConstructionModel) | López de Prado: beats Markowitz OOS |
| Execution model | VolumeWeightedAveragePriceExecutionModel | Johnson: minimises market impact |
| Validation | IS → WFO → Monte Carlo → CPCV → OOS | Davey + López de Prado combined |

---

## 🏗️ Repository Structure

```
satyamohapatro1234/Lean/                ← This repo
│
├── engine/
│   └── Lean/                           ← git submodule → github.com/QuantConnect/Lean
│       ├── Algorithm.Python/           ← Python algorithm support
│       ├── Launcher/                   ← Build target: QuantConnect.Lean.Launcher.exe
│       ├── Data/                       ← LEAN reference data (symbol-properties, market-hours)
│       └── QuantConnect.Lean.sln       ← Build this with: dotnet build
│
├── lean-data/                          ← LEAN /Data folder (git-ignored, populated by pipeline)
│   ├── equity/india/daily/             ← Bhavcopy → LEAN zip format
│   ├── equity/india/minute/            ← Dhan intraday → LEAN zip format
│   ├── forex/oanda/minute/             ← OANDA forex data
│   ├── equity/usa/minute/              ← Alpaca US equity data
│   ├── symbol-properties/              ← Copied from engine/Lean/Data/ at setup
│   └── market-hours/                   ← Copied from engine/Lean/Data/ at setup
│
├── lean-results/                       ← Backtest outputs (git-ignored)
│
├── platform/                           ← Our platform code
│   ├── data-pipeline/                  ← Data download and ingestion
│   │   ├── india/
│   │   │   ├── bhavcopy_downloader.py  ← NSE Bhavcopy EOD (1 file = all stocks)
│   │   │   ├── dhan_intraday.py        ← Dhan API → SQLite job queue → QuestDB
│   │   │   └── lean_writer.py          ← QuestDB → LEAN zip format
│   │   ├── international/
│   │   │   ├── alpaca_downloader.py    ← Alpaca US equity data
│   │   │   ├── oanda_downloader.py     ← OANDA forex data
│   │   │   └── lean_writer_intl.py     ← International → LEAN zip format
│   │   └── daily_updater.py            ← Cron: runs all downloaders nightly
│   │
│   ├── instrument-master/              ← Symbol mapping and reference data
│   │   ├── schema.sql                  ← SQLite schema
│   │   ├── india/
│   │   │   ├── dhan_parser.py          ← Dhan CSV → SQLite
│   │   │   └── nse_fo_parser.py        ← NSE F&O instrument master
│   │   └── international/
│   │       ├── alpaca_symbols.py       ← Alpaca symbol list → SQLite
│   │       └── oanda_pairs.py          ← OANDA pairs → SQLite
│   │
│   ├── symbol-mapper/                  ← Universal symbol translation
│   │   └── universal_mapper.py         ← Dhan ID ↔ LEAN Symbol ↔ Alpaca ID ↔ OANDA pair
│   │
│   ├── strategies/                     ← LEAN Python algorithms
│   │   ├── spider-wave/
│   │   │   ├── main.py                 ← SpiderWaveAlgorithm (QCAlgorithm subclass)
│   │   │   ├── fee_model.py            ← DhanFeeModel + AlpacaFeeModel (versioned)
│   │   │   └── indicators.py           ← Custom wave indicators
│   │   └── base_algorithm.py           ← Shared base for all strategies
│   │
│   ├── engine-wrapper/                 ← LEAN subprocess communication
│   │   ├── run_backtest.py             ← Write config.json → launch LEAN → parse results
│   │   ├── run_forward_test.py         ← Paper trading runner
│   │   └── lean_config_builder.py      ← Builds lean-config.json for each run
│   │
│   ├── brokers/                        ← Broker integrations (abstract interface)
│   │   ├── base_broker.py              ← Abstract: authenticate, order, positions, ticks
│   │   ├── india/
│   │   │   ├── dhan/
│   │   │   ├── zerodha/
│   │   │   ├── upstox/
│   │   │   ├── angel_one/
│   │   │   └── fyers/
│   │   └── international/
│   │       ├── alpaca/                 ← Uses LEAN's existing Alpaca plugin
│   │       ├── oanda/                  ← Uses LEAN's existing OANDA plugin
│   │       └── interactive_brokers/    ← Uses LEAN's existing IB plugin
│   │
│   ├── scanner/                        ← Market scanner engine
│   │   ├── engine.py                   ← Runs criteria against QuestDB in parallel
│   │   ├── criteria/                   ← Scanner criteria definitions
│   │   │   ├── technical.py            ← RSI, MACD, BB, SMA crossovers
│   │   │   ├── fundamental.py          ← P/E, volume, market cap
│   │   │   └── options.py              ← OI buildup, IV percentile, PCR
│   │   └── alerts.py                   ← Alert dispatch (WebSocket + notification)
│   │
│   ├── agents/                         ← LangGraph AI agent system
│   │   ├── llm_router.py               ← Claude → Ollama fallback
│   │   ├── supervisor.py               ← Single entry point, routes to specialist agents
│   │   ├── memory.db                   ← SQLite LangGraph checkpoint store (git-ignored)
│   │   ├── research/                   ← Layer 1: runs 6:00–9:15 AM pre-market
│   │   │   ├── market_scan.py          ← OI anomalies, IV, wave confluence
│   │   │   ├── news_analyst.py         ← NSE announcements → portfolio impact
│   │   │   └── regulatory_watcher.py   ← SEBI/NSE circulars, auto-update fee schedules
│   │   ├── analysis/                   ← Layer 2: runs nightly or on-demand
│   │   │   ├── regime_detector.py      ← HMM + VIX → market regime
│   │   │   ├── feature_engineer.py     ← Dollar bars, fractional diff, MDI/MDA
│   │   │   ├── validation_pipeline.py  ← Automated 5-gate Davey validation
│   │   │   ├── portfolio_rebalancer.py ← Carver buffered + CPPI + India tax gate
│   │   │   └── capacity_analyst.py     ← Max capital before slippage erodes edge
│   │   ├── decision/                   ← Layer 3: during/after market hours
│   │   │   ├── strategy_router.py      ← Capital allocation per regime (Carver)
│   │   │   ├── strategy_registry.py    ← SQLite: strategy metadata + weights
│   │   │   ├── spider_wave_agent.py    ← Runs Spider Wave via LEAN
│   │   │   ├── strategy_advisor.py     ← Explains strategy decisions in plain English
│   │   │   ├── portfolio_coach.py      ← Portfolio health + rebalancing suggestions
│   │   │   ├── optimizer_agent.py      ← Grid/Euler parameter search + Monte Carlo
│   │   │   └── backtest_orchestrator.py ← NL query → LEAN backtest → formatted result
│   │   ├── execution/                  ← Layer 4: on user action only
│   │   │   ├── order_assist.py         ← NL → order params → margin check → confirm
│   │   │   └── journal_agent.py        ← Records every trade decision with context
│   │   └── monitor/                    ← Layer 5: always-on, NO LLM
│   │       ├── risk_guard.py           ← Event-driven tick monitoring, <200ms
│   │       └── risk_analyst.py         ← Deep risk analysis, on-demand only
│   │
│   ├── api/                            ← FastAPI backend
│   │   ├── main.py                     ← App entry point
│   │   ├── routers/
│   │   │   ├── market_data.py          ← REST: OHLCV, tick snapshots
│   │   │   ├── orders.py               ← REST: order CRUD
│   │   │   ├── portfolio.py            ← REST: positions, P&L, holdings
│   │   │   ├── backtests.py            ← REST: submit, status, results
│   │   │   ├── scanner.py              ← REST: run scan, get alerts
│   │   │   ├── agents.py               ← REST: agent chat, agent status
│   │   │   └── settings.py             ← REST: broker config, user preferences
│   │   ├── websocket/
│   │   │   ├── manager.py              ← Multi-client WebSocket manager
│   │   │   ├── tick_dispatcher.py      ← Redis sub → WebSocket broadcast
│   │   │   └── handlers.py             ← WS message handlers
│   │   └── mcp_server.py               ← MCP server: single "trading_system" tool
│   │
│   └── config/                         ← Configuration files (versioned)
│       ├── fee_schedules.json          ← STT rates by date (SEBI changes)
│       ├── nse_holidays.json           ← NSE trading calendar
│       └── lot_size_history.json       ← Lot sizes by date (SEBI Dec 2024 changes)
│
├── frontend/                           ← React trading terminal
│   ├── src/
│   │   ├── lib/
│   │   │   ├── websocket.ts            ← Singleton WebSocket manager (NOT a React component)
│   │   │   └── api.ts                  ← REST client
│   │   ├── components/
│   │   │   ├── chart/                  ← KLineChart Pro wrapper
│   │   │   ├── watchlist/              ← Direct DOM price updates
│   │   │   ├── order-entry/            ← Order form + margin check
│   │   │   ├── positions/              ← AG Grid positions table
│   │   │   ├── scanner/                ← Scanner panel + results
│   │   │   ├── backtest/               ← Backtest results viewer
│   │   │   ├── options-chain/          ← Options chain + IV surface (D3.js)
│   │   │   └── ai-assistant/           ← LangGraph agent chat panel
│   │   └── stores/
│   │       └── trading.ts              ← Zustand store (medium-speed data only)
│   └── package.json
│
├── tests/                              ← Test suites
│   ├── conftest.py                     ← pytest markers: requires_lean, requires_questdb
│   ├── test_lean_format.py             ← LEAN price × 10000, timestamp format
│   ├── test_fee_model.py               ← STT pre/post Oct 2024
│   ├── test_lot_sizes.py               ← Lot sizes pre/post Dec 2024
│   ├── test_symbol_mapper.py           ← Round-trip: Dhan ↔ LEAN ↔ Alpaca
│   ├── test_bhavcopy.py               ← Bhavcopy parser correctness
│   └── test_scanner.py                 ← Scanner criteria correctness
│
├── setup/                              ← One-time setup scripts
│   ├── build_lean.sh                   ← cd engine/Lean && dotnet build
│   ├── seed_lean_data.sh               ← Copy symbol-properties + market-hours
│   ├── install_questdb.sh              ← Start QuestDB natively
│   └── create_venvs.sh                 ← Create .venv (3.14) and .venv311 (3.11)
│
├── .gitmodules                         ← Declares engine/Lean as submodule
├── .gitignore                          ← lean-data/, lean-results/, *.db, *.sqlite
├── BLUEPRINT.md                        ← This file
├── PLAN.md                             ← Phase-by-phase development plan
├── CONTEXT.md                          ← Project history, decisions, mistakes
├── DECISIONS.md                        ← Quick lookup for all technology decisions
├── PROGRESS.md                         ← Live phase/step tracker
├── AGENT_INSTRUCTIONS.md               ← Rules for AI coding agents
└── README.md                           ← Public-facing description

```

---

## 🌐 The Two Markets — UI and Data Design

### Indian Market (NSE/BSE)
User connects their own broker. Platform does NOT hold Indian market data centrally — it downloads from the user's broker via their API key.

**Indian UI specifics:**
- Market hours: 9:15 AM – 3:30 PM IST
- Instruments: Equities, F&O (NSE), Currency Derivatives (NSE CDS), Commodities (MCX)
- Key views: Option chain with OI + IV, PCR, Open Interest buildup heat map
- Lot sizes change: must be date-aware (Dec 2024: Nifty 50→25, BankNifty 15→30)
- Expiry calendar: Weekly (Nifty50 on Thursday, Sensex on Tuesday post-Nov 2024), monthly
- STT display: Show gross vs net P&L after SEBI charges (STT changed Oct 2024)
- Index display: Nifty 50, Bank Nifty, Nifty IT, India VIX
- Market depth: 5-level bid/ask (not Level 2 for most retail users)

**Indian data flow:**
```
Dhan/Zerodha/Upstox WebSocket → Redis pub/sub → FastAPI WebSocket → Frontend
NSE Bhavcopy (free, 1 file/day) → QuestDB → LEAN /Data → Backtest
Dhan intraday API (rate-limited, resumable) → QuestDB → LEAN /Data → Backtest
```

### International Market (US Equities + Forex)
Platform provides data via Alpaca (US stocks) and OANDA (forex) — **free when user has an account**.

**US Equity UI specifics:**
- Market hours: 9:30 AM – 4:00 PM ET (pre/post market 4 AM – 8 PM ET via Alpaca)
- Instruments: Stocks, ETFs, Options (US-listed)
- Key views: Standard L1 quotes + option chain (OPRA data via Alpaca)
- Extended hours trading supported (Alpaca provides)
- Pattern Day Trader rule: Flag if user makes 4+ day trades in 5 days (< $25K account)

**Forex UI specifics:**
- 24/5 market (Sunday 5 PM ET – Friday 5 PM ET)
- 70+ currency pairs via OANDA
- Pip display, spread indicator, rollover (swap) costs
- Leverage display: 50:1 max (US CFTC regulated)

**International data flow:**
```
Alpaca WebSocket → Redis pub/sub → FastAPI WebSocket → Frontend (US equities)
OANDA Streaming API → Redis pub/sub → FastAPI WebSocket → Frontend (forex)
Alpaca REST (10yr 1-min historical, free with account) → QuestDB → LEAN /Data
OANDA REST (historical since 2007, 71 pairs, free with account) → QuestDB → LEAN /Data
```

---

## 📊 Complete Storage Architecture

### Storage Layers
```
LAYER 1 — Hot Store (Redis)
  Purpose: Real-time tick distribution, pub/sub
  What lives here:
    - Latest tick per symbol: redis HASH  tick:{symbol} → {ltp, bid, ask, vol, ts}
    - Channel per symbol: redis PUB/SUB  ticks:{symbol}
    - Session state: redis STRING  session:{user_id} → JSON
    - Rate limiter tokens: redis SORTED SET  ratelimit:{broker}:{endpoint}
  Retention: In-memory only, no persistence needed for tick data
  Pattern: Broker WebSocket → Python subscriber → Redis PUBLISH → FastAPI fans out to clients

LAYER 2 — Time-Series Store (QuestDB)
  Purpose: OHLCV storage, queryable by time range, symbol, resolution
  Tables:
    ohlcv_india_daily       ← NSE Bhavcopy EOD (symbol, date, open, high, low, close, vol, oi)
    ohlcv_india_minute      ← Dhan intraday 1-min bars (same schema + oi)
    ohlcv_us_daily          ← Alpaca EOD
    ohlcv_us_minute         ← Alpaca 1-min bars
    ohlcv_forex_minute      ← OANDA 1-min bars
    ohlcv_india_tick        ← Raw ticks from broker WS (optional, for HFT analysis)
    backtest_trades         ← All trades from all backtests (for journal queries)
    live_trades             ← Live execution log
  Ingestion: ILP protocol on port 9009 (fastest path)
  Queries: PGwire on port 8812 (psycopg2 compatible)
  Port 9000: Web console for debugging

LAYER 3 — Relational Store (SQLite)
  Purpose: Reference data, job queues, agent state
  Databases:
    instruments.db          ← Instrument master (symbol maps, lot sizes, fee schedules)
    jobs.db                 ← Download job queue (status: pending/completed/failed)
    agents/memory.db        ← LangGraph checkpoint store (thread/session/long-term memory)
    strategy_registry.db    ← Strategy metadata, weights, backtest history
    journal.db              ← Trade journal (every decision with full context)

LAYER 4 — LEAN Data Folder (Filesystem)
  Purpose: LEAN engine's native data format
  Location: lean-data/
  Format: ZIP archives per symbol per day, CSV inside
    equity/india/daily/{symbol}/{YYYYMMDD}_trade.zip   ← YYYYMMDD 00:00 timestamp format
    equity/india/minute/{symbol}/{YYYYMMDD}_trade.zip  ← ms-since-midnight timestamp
    forex/oanda/minute/{pair}/{YYYYMMDD}_quote.zip
    equity/usa/minute/{symbol}/{YYYYMMDD}_trade.zip
  LEAN price format: int(price × 10000) — ₹94.00 → 940000
  Reference files (one-time copy from engine/Lean/Data/):
    lean-data/symbol-properties/symbol-properties-database.csv
    lean-data/market-hours/market-hours-database.json
    lean-data/map-files/india/     ← For survivorship bias (delistings)
    lean-data/factor-files/india/  ← Split/dividend adjustment factors
```

---

## 🔄 Real-Time Data Architecture

### The Critical Insight (from research)
**Never put live tick prices into React state.** At 100–200 ticks/second this causes 100–200 re-renders/second. The UI freezes.

### Three-Tier Data Model
```
HOT DATA (ticks, 100–200/sec)
  Path: Broker WS → Redis PUBLISH → FastAPI WS → WebSocket.ts singleton → DOM mutation
  In frontend: wsManager.subscribe(symbol, (price) => { domElement.textContent = price })
  Never touches React state. Never triggers a render.

MEDIUM DATA (positions, P&L, orders — updates every 5 sec)
  Path: FastAPI REST → Zustand store → React renders
  Components that read: PositionsPanel, OrderHistory, P&LSummary

COLD DATA (settings, config, backtest results — changes on user action)
  Path: FastAPI REST → React useState
  Components that read: SettingsScreen, BacktestViewer, StrategyConfig
```

### WebSocket Connection Architecture
```
Frontend (N clients)
  ↑ WebSocket connections
FastAPI WebSocket Manager
  ← subscribes to →
Redis pub/sub channels (one per symbol)
  ← publishes to →
Python Tick Aggregator (one per broker)
  ← receives from →
Broker WebSocket (Dhan / Alpaca / OANDA)

Rule: ONE broker connection per broker, no matter how many frontend clients
Rule: Redis fan-out to all clients who subscribed to that symbol
```

---

## 📡 Scanner Architecture

A scanner runs a set of **criteria** against **all instruments** and returns matches.

### Scanner Design
```
ScanRequest {
  universe: "nse_fno" | "nse_all" | "us_sp500" | "us_all" | "forex"
  criteria: [
    { type: "technical", indicator: "RSI", condition: "< 30", timeframe: "daily" },
    { type: "technical", indicator: "Volume", condition: "> 2x average 20d" },
    { type: "options",   indicator: "OI", condition: "> 20% buildup" },
    { type: "fundamental", indicator: "Market Cap", condition: "> 1000 Cr" }
  ]
  sort_by: "RSI asc"
  limit: 50
}
```

### How It Runs
```python
# Scanner Engine Pattern
class ScannerEngine:
    def run(self, request: ScanRequest) -> List[ScanResult]:
        # 1. Get universe from instrument master (SQLite)
        symbols = self.instrument_master.get_universe(request.universe)
        
        # 2. Batch query QuestDB for latest OHLCV + indicators
        # QuestDB materialized views pre-compute RSI, MACD, BB daily
        # Single SQL query returns all symbols that match technical criteria
        
        # 3. Apply option criteria (from latest OI snapshot in QuestDB)
        
        # 4. Sort + limit + return

# QuestDB materialized view example:
# CREATE MATERIALIZED VIEW mv_rsi_daily AS
#   SELECT symbol, timestamp,
#     avg(close) OVER (PARTITION BY symbol ORDER BY timestamp ROWS 14 PRECEDING) as rsi_raw
#   FROM ohlcv_india_daily
# This pre-computes so scanner queries are instant
```

### Scanner Triggers
- **Real-time scan:** Runs every N minutes during market hours (configurable, default 15min)
- **Pre-market scan:** Runs at 9:00 AM IST from yesterday's close data
- **On-demand:** User hits "Scan Now" button
- **Alert scan:** Continuous monitoring for a specific condition on a specific symbol

---

## 🤖 Agent Architecture — 19 Agents in 5 Layers

### LLM Routing — Claude → Ollama Fallback
```python
class LLMRouter:
    """Try Claude first. If unavailable or timeout, fall back to Ollama."""
    
    def __init__(self):
        self.claude = ChatAnthropic(model="claude-sonnet-4-20250514", timeout=30)
        self.ollama = ChatOllama(model="qwen2.5:14b", base_url="http://localhost:11434")
    
    def get_llm(self, task_type: str = "general"):
        """Returns (llm, is_online) tuple."""
        try:
            # Quick health check — if Claude responds within 3 seconds, use it
            self.claude.invoke([HumanMessage(content="ping")], timeout=3)
            return self.claude, True
        except Exception:
            return self.ollama, False
```

### The 19 Agents
```
SUPERVISOR (single entry point)
    ↓ routes to →
┌─────────────────────────────────────────────────────────────────┐
│ RESEARCH LAYER (6:00–9:15 AM pre-market)                        │
│   MarketScan         → OI buildup, IV anomalies, wave signals   │
│   NewsAnalyst        → Corporate announcements → portfolio impact│
│   RegulatoryWatcher  → SEBI/NSE circulars, auto-update fees     │
├─────────────────────────────────────────────────────────────────┤
│ ANALYSIS LAYER (nightly / on-demand)                            │
│   RegimeDetector     → HMM + VIX → TRENDING/CHOPPY/HIGH_VOL    │
│   FeatureEngineer    → Dollar bars, fractional diff, MDI/MDA    │
│   ValidationPipeline → Automated 5-gate Davey validation        │
│   PortfolioRebalancer→ Carver buffered + CPPI + India tax gate  │
│   CapacityAnalyst    → Max capital before slippage erodes edge  │
├─────────────────────────────────────────────────────────────────┤
│ DECISION LAYER (during/after market hours)                      │
│   StrategyRouter     → Capital allocation per regime (Carver)   │
│   SpiderWaveAgent    → Spider Wave via LEAN                     │
│   StrategyAdvisor    → Explains strategy decisions plainly      │
│   PortfolioCoach     → Portfolio health + rebalancing advice    │
│   OptimizerAgent     → Grid/Euler search + Monte Carlo          │
│   BacktestOrchestrator → NL → LEAN backtest → formatted result │
├─────────────────────────────────────────────────────────────────┤
│ EXECUTION LAYER (on user action, always requires confirmation)  │
│   OrderAssist        → NL → order params → margin check → send  │
│   JournalAgent       → Records every decision with full context │
├─────────────────────────────────────────────────────────────────┤
│ MONITOR LAYER (always-on, ZERO LLM calls)                       │
│   RiskGuard          → Event-driven, <200ms, auto-liquidate 5%  │
│   RiskAnalyst        → Deep risk analysis, on-demand only       │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Time Schedule (Durenard's priority queue principle)
```
06:00–09:15  Pre-market batch (LLM-powered, offline fine)
  RegulatoryWatcher → scrape SEBI/NSE, update fee_schedules.json if changed
  RegimeDetector    → calculate today's regime from yesterday's close
  MarketScan        → OI, IV, wave signals (1 LLM call for summary)
  NewsAnalyst       → overnight announcements for held positions

09:15–15:30  Market hours (MINIMAL agent activity — no analytical LLM calls)
  RiskGuard         → event-driven per tick, ~0.1ms, pure Python, no LLM
  StrategyRouter    → recalculates weights every 60 seconds, pure Python
  Supervisor        → only when user sends a message
  OrderAssist       → only when user types an order

15:30–18:00  Post-market daily batch
  FeatureEngineer   → rebuild ML features with today's data
  JournalAgent      → record today's trades
  PortfolioRebalancer → check drift vs Carver buffer

Nightly / Weekend (heavy batch — on-demand only)
  ValidationPipeline → full 5-gate test suite (hours)
  OptimizerAgent    → parameter search (hours)
  BacktestOrchestrator → full historical backtest (minutes)
```

### A2A Protocol Integration (Phase 3+)
Async agents expose A2A endpoints. The Supervisor discovers them via Agent Cards.

```
AGENT CARDS (published by each async agent):
  /.well-known/agent.json on each agent's HTTP server

AGENTS USING A2A (async, no latency requirement):
  BacktestOrchestrator  → port 8001
  OptimizerAgent        → port 8002
  ValidationPipeline    → port 8003
  MarketScan            → port 8004
  NewsAnalyst           → port 8005

AGENTS NOT USING A2A (stay in-process, latency-critical):
  RiskGuard             → in-process, per-tick, no network hops
  StrategyRouter        → in-process, every 60s, pure Python
  OrderAssist           → in-process, user-facing
```

---

## 🖥️ Frontend Architecture — Complete Design

### Layout: 3-Panel Professional Terminal
```
┌─────────────────────────────────────────────────────────────────────┐
│ TOP BAR: Market status | Time (IST + ET) | Account selector        │
├──────┬──────────────────────────────────────────┬───────────────────┤
│ LEFT │ MAIN CENTER                              │ RIGHT PANEL       │
│      │                                          │                   │
│ Watch│ KLineChart Pro (full-screen chart)       │ Order Entry       │
│ list │ Timeframe: 1m 5m 15m 1h 1d              │ ──────────────    │
│      │ Indicators: MA, MACD, RSI, Volume       │ Positions (Zustand│
│      │ Drawing tools: trend, fib, levels       │ Zustand+5s poll)  │
│      │ Multi-chart: 1, 2, or 4 charts          │ ──────────────    │
│      │                                          │ AI Assistant Chat │
│      ├──────────────────────────────────────────┤                   │
│      │ BOTTOM TABS:                             │                   │
│      │ Orders | Portfolio | Backtest | Scanner  │                   │
└──────┴──────────────────────────────────────────┴───────────────────┘
```

### Market Switcher (India ↔ International)
```
Header contains: [🇮🇳 India ▼] dropdown
  Options:
    🇮🇳 India (NSE/BSE)     → shows IST time, ₹, F&O chain, OI view
    🇺🇸 US Equities (Alpaca) → shows ET time, $, US options, PDT warning
    💱 Forex (OANDA)         → shows 24h status, pip display, swap rates

When market changes:
  - Chart reloads with market-appropriate data
  - Order panel shows market-specific order types (MIS/CNC/NRML for India, GTC/GTD for US)
  - Scanner universe changes
  - Positions panel shows relevant holdings only
```

### Critical Frontend Rules
```typescript
// ❌ NEVER — causes 200 re-renders/second, freezes browser
ws.onmessage = (tick) => { setLastPrice(tick.ltp) }

// ✅ ALWAYS — direct DOM, bypasses React entirely
class WebSocketManager {
  private callbacks = new Map<string, (price: number) => void>()
  
  subscribe(symbol: string, el: HTMLElement) {
    this.callbacks.set(symbol, (price) => {
      el.textContent = price.toFixed(2)
      el.classList.toggle('flash-green', price > el.dataset.prev)
    })
  }
}

// WATCHLIST ITEM (direct DOM, not React):
// <span id="ltp-NIFTY" data-prev="24350">24350.00</span>
// wsManager.subscribe("NIFTY", document.getElementById("ltp-NIFTY"))
```

---

## 📋 API Endpoint Design — Complete

### REST API (FastAPI)

#### Market Data
```
GET  /api/v1/market/quote/{symbol}           → Latest L1 quote
GET  /api/v1/market/ohlcv/{symbol}           → Historical OHLCV (from QuestDB)
     ?resolution=1min&from=2024-01-01&to=2024-12-31
GET  /api/v1/market/options-chain/{symbol}   → Full option chain + OI + IV
     ?expiry=2024-12-26
GET  /api/v1/market/indices                  → Index list + values
GET  /api/v1/market/status                   → Market open/close status per exchange
GET  /api/v1/market/calendar/{exchange}      → Trading calendar + holidays
```

#### Orders
```
POST /api/v1/orders                          → Place order (requires margin check first)
GET  /api/v1/orders                          → Order history (with filters)
GET  /api/v1/orders/{order_id}              → Single order status
PUT  /api/v1/orders/{order_id}              → Modify pending order
DEL  /api/v1/orders/{order_id}              → Cancel pending order
POST /api/v1/orders/margin-check             → Pre-margin check before placing
     Body: { symbol, quantity, order_type, price, broker }
```

#### Portfolio
```
GET  /api/v1/portfolio/positions             → Open positions across all brokers
GET  /api/v1/portfolio/holdings              → Long-term equity holdings
GET  /api/v1/portfolio/pnl                   → Today's P&L + overall
GET  /api/v1/portfolio/trades                → Trade history
GET  /api/v1/portfolio/risk                  → Current risk metrics (VaR, Greeks)
```

#### Backtesting
```
POST /api/v1/backtests                       → Submit backtest job
     Body: { strategy, universe, start, end, params, broker_model }
GET  /api/v1/backtests/{backtest_id}        → Job status + progress
GET  /api/v1/backtests/{backtest_id}/results → Full results (equity curve, stats, trades)
GET  /api/v1/backtests/{backtest_id}/chart   → Equity curve chart data
GET  /api/v1/backtests                       → List all past backtests
DEL  /api/v1/backtests/{backtest_id}        → Cancel running backtest
```

#### Scanner
```
POST /api/v1/scanner/run                     → Run one-time scan
     Body: { universe, criteria, sort_by, limit }
GET  /api/v1/scanner/results/{scan_id}      → Scan results
GET  /api/v1/scanner/presets                 → Pre-built scanner templates
POST /api/v1/scanner/alerts                  → Create ongoing alert
GET  /api/v1/scanner/alerts                  → List active alerts
DEL  /api/v1/scanner/alerts/{alert_id}      → Remove alert
```

#### Agents
```
POST /api/v1/agents/chat                     → Send message to Supervisor
     Body: { message, context? }
GET  /api/v1/agents/chat/{session_id}       → Chat history
GET  /api/v1/agents/status                   → All agent statuses + last run
POST /api/v1/agents/backtest-orchestrator   → Direct backtest via agent
POST /api/v1/agents/regime                   → Get current regime assessment
```

#### Settings & Broker Config
```
GET  /api/v1/settings/brokers               → Connected brokers + status
POST /api/v1/settings/brokers               → Add broker connection
DEL  /api/v1/settings/brokers/{broker_id}  → Remove broker
GET  /api/v1/settings/markets               → Enabled markets
GET  /api/v1/settings/strategies            → Registered strategies + their status
```

### WebSocket API
```
Connect: ws://localhost:8000/ws

Subscribe to ticks:
  → SEND: { "type": "subscribe", "symbols": ["NIFTY", "BANKNIFTY", "AAPL", "EURUSD"] }
  ← RECV: { "type": "tick", "symbol": "NIFTY", "ltp": 24350.50, "bid": 24349, "ask": 24351, "ts": 1234567890 }

Subscribe to alerts:
  → SEND: { "type": "subscribe_alerts", "user_id": "..." }
  ← RECV: { "type": "alert", "alert_id": "...", "symbol": "...", "message": "..." }

Backtest progress:
  ← RECV: { "type": "backtest_progress", "backtest_id": "...", "pct": 45, "status": "running" }

Agent response (streaming):
  ← RECV: { "type": "agent_chunk", "session_id": "...", "content": "Spider Wave signal..." }
```

---

## ⚙️ LEAN Engine Integration — Correct Pattern

### What LEAN is and isn't
- LEAN is C#. Python algorithms run inside LEAN via Python.NET bridge.
- LEAN **cannot be imported** as a Python package.
- All LEAN interaction is via subprocess: write config → launch exe → read result.

### The Subprocess Pattern
```python
# engine-wrapper/run_backtest.py

import subprocess
import json
import os

LEAN_EXE = "engine/Lean/Launcher/bin/Release/QuantConnect.Lean.Launcher.exe"
LEAN_DATA = "lean-data"

def run_backtest(strategy: str, start: str, end: str, symbols: list) -> dict:
    # 1. Write config
    config = {
        "algorithm-type-name": strategy,
        "algorithm-language": "Python",
        "algorithm-location": f"platform/strategies/{strategy.lower()}/main.py",
        "data-folder": LEAN_DATA,
        "results-destination-folder": "lean-results",
        "start-date": start,
        "end-date": end,
        "cash": 1000000,
        "environment": "backtesting",
        "log-handler": "QuantConnect.Logging.CompositeLogHandler"
    }
    
    config_path = "lean-results/lean-config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    # 2. Launch LEAN — critical: set PYTHONNET_PYDLL
    env = os.environ.copy()
    env["PYTHONNET_PYDLL"] = "python311.dll"  # Must match .venv311
    
    result = subprocess.run(
        [LEAN_EXE, "--config", config_path],
        capture_output=True, text=True, env=env,
        cwd="."
    )
    
    # 3. Parse results
    result_file = f"lean-results/{strategy}.json"
    with open(result_file) as f:
        return json.load(f)
```

### LEAN Data Format Rules (Non-Negotiable)
```
Daily equity CSV (inside zip):
  Format: "YYYYMMDD 00:00,open,high,low,close,volume"
  Example: "20240101 00:00,940000,945000,938000,942500,1250000"
  
Minute equity CSV (inside zip):
  Format: "ms_since_midnight,open,high,low,close,volume"
  Example: "33300000,940000,940500,939800,940200,125000"
  
All prices: int(price_in_rupees × 10000)
  ₹94.25 → 942500

Zip file path for daily India:
  lean-data/equity/india/daily/{ticker_lowercase}/{YYYYMMDD}_trade.zip
  
Zip file path for minute India:
  lean-data/equity/india/minute/{ticker_lowercase}/{YYYYMMDD}_trade.zip

Reference files MUST exist (one-time copy at setup):
  lean-data/symbol-properties/symbol-properties-database.csv
  lean-data/market-hours/market-hours-database.json
```

---

## 🔐 Security Rules

```
1. ALL API keys in environment variables — NEVER in code
2. Indian broker tokens rotate every 24h (SEBI mandate) — automated Playwright refresh at 6AM
3. Alpaca API key in .env — LEAN reads from config, not from code
4. OANDA access token in .env
5. No raw order placement — every order requires:
   a. Pre-margin check (broker API call)
   b. Human confirmation dialog
   c. OrderAssist records the decision to journal
6. RiskGuard auto-liquidates at 5% portfolio drawdown — this is the ONLY auto-execution
7. All agent memory is local (SQLite) — no trading data sent to cloud LLMs if offline
8. LLMRouter: market-hours activity uses Ollama by default (trading data stays local)
```

---

## 📐 Build Phases — Overview

```
PHASE 0 — LEAN + Data Foundation        (Weeks 1–4)
  ├── 0.1  Repository setup (submodule, venvs, LEAN build)
  ├── 0.2  Instrument master (India: Dhan + NSE; International: Alpaca + OANDA)
  ├── 0.3  Bhavcopy downloader (India EOD)
  ├── 0.4  Dhan intraday downloader (resumable job queue)
  ├── 0.5  Alpaca historical downloader (US EOD + minute)
  ├── 0.6  OANDA historical downloader (forex)
  ├── 0.7  LEAN data writer (QuestDB → LEAN zip format, both markets)
  ├── 0.8  Symbol mapper (universal: Dhan ↔ LEAN ↔ Alpaca ↔ OANDA)
  ├── 0.9  Spider Wave MVP strategy (runs inside LEAN)
  ├── 0.10 Engine wrapper + first India backtest
  ├── 0.11 First US backtest (Alpaca data + AlpacaBrokerageModel)
  ├── 0.12 First Forex backtest (OANDA data + OandaBrokerageModel)
  ├── 0.13 Fee models (DhanFeeModel + AlpacaFeeModel, versioned by date)
  ├── 0.14 Data quality checks
  └── 0.15 Streamlit monitoring dashboard (developer tool, not final UI)

PHASE 1 — Strategy Validation           (Weeks 5–10)
  ├── 1.1  In-sample backtest (2019–2021, F&O universe)
  ├── 1.2  Walk forward optimization
  ├── 1.3  Monte Carlo (10,000 shuffles)
  ├── 1.4  CPCV (combinatorial purged cross-validation)
  ├── 1.5  Out-of-sample (2022–2024)
  └── 1.6  Carver forecast scaling (continuous signal −20/+20)

PHASE 2 — Live Broker Integration       (Weeks 11–14)
  ├── 2.1  Dhan WebSocket client (Indian live ticks)
  ├── 2.2  Dhan order API + margin model
  ├── 2.3  Alpaca WebSocket client (US live ticks)
  ├── 2.4  OANDA streaming API client (forex live ticks)
  ├── 2.5  Redis tick distribution layer
  ├── 2.6  Paper trading run — India (14 days)
  └── 2.7  Paper trading run — US + Forex (14 days)

PHASE 3 — FastAPI Backend + Core Agents (Weeks 15–20)
  ├── 3.1  FastAPI application structure
  ├── 3.2  WebSocket manager (multi-client, symbol subscription)
  ├── 3.3  LLMRouter (Claude → Ollama fallback)
  ├── 3.4  Supervisor agent + SQLite memory
  ├── 3.5  RiskGuard + StrategyRouter (always-on processes)
  ├── 3.6  BacktestOrchestrator + OptimizerAgent
  ├── 3.7  MCP server (single "trading_system" tool)
  └── 3.8  A2A endpoints for async agents

PHASE 4 — Scanner + Options Intelligence(Weeks 21–24)
  ├── 4.1  Scanner engine + criteria system
  ├── 4.2  QuestDB materialized views for scanner performance
  ├── 4.3  Options chain data (India: from Dhan; US: from Alpaca OPRA)
  ├── 4.4  Options analytics backend (IV surface, greeks, OI)
  └── 4.5  WaveSignal + StrategyAdvisor agents

PHASE 5 — More Indian Brokers + All 19 Agents (Weeks 25–30)
  ├── 5.1  Zerodha integration (uses existing LEAN plugin)
  ├── 5.2  Upstox integration
  ├── 5.3  Angel One integration
  ├── 5.4  Fyers integration
  ├── 5.5  RegimeDetector (HMM)
  ├── 5.6  FeatureEngineer (dollar bars, fractional diff)
  ├── 5.7  ValidationPipeline (automated 5-gate)
  ├── 5.8  PortfolioRebalancer (Carver + CPPI + tax gate)
  ├── 5.9  Remaining agents: MarketScan, NewsAnalyst, RegulatoryWatcher,
  │         CapacityAnalyst, PortfolioCoach, JournalAgent, RiskAnalyst
  └── 5.10 Agent time schedule automation (cron)

PHASE 6 — Interactive Brokers (Global)  (Weeks 31–34)
  ├── 6.1  IB integration (uses existing LEAN plugin)
  ├── 6.2  Global historical data (IB data provider)
  ├── 6.3  Multi-currency portfolio support
  └── 6.4  Global scanner (cross-market)

PHASE 7 — React Trading Terminal        (Weeks 35–46)
  ├── 7.1  Design system (Tailwind, shadcn/ui, design tokens)
  ├── 7.2  Layout shell (3-panel, collapsible, responsive)
  ├── 7.3  Performance architecture (WebSocket singleton + DOM mutation)
  ├── 7.4  Market switcher (India / US / Forex)
  ├── 7.5  Watchlist (direct DOM, CSS flash, drag to reorder)
  ├── 7.6  KLineChart Pro (historical REST + live WebSocket updates)
  ├── 7.7  Order entry panel (market-specific order types, margin check)
  ├── 7.8  Positions + orders (AG Grid, virtualised, direct DOM for P&L)
  ├── 7.9  Backtest results viewer (Recharts equity curve, stats table)
  ├── 7.10 Scanner panel (criteria builder, results table, alert management)
  ├── 7.11 Options chain view (India OI + IV; US: OPRA greeks; D3 IV surface)
  ├── 7.12 AI assistant panel (streaming LangGraph agent chat)
  └── 7.13 Settings (broker connections, strategy config, market enable/disable)

PHASE 8 — Open Source Launch            (Weeks 47–52)
  ├── 8.1  Production environment setup (all services native, no Docker)
  ├── 8.2  Complete documentation (setup guide, API reference, strategy guide)
  ├── 8.3  GitHub release + community setup
  └── 8.4  Demo video + launch
```

---

## 🛠️ How to Set Up (One-Time)

```bash
# 1. Clone this repo WITH the LEAN submodule
git clone --recurse-submodules https://github.com/satyamohapatro1234/Lean.git
cd Lean

# 2. Build LEAN from source
cd engine/Lean
dotnet build QuantConnect.Lean.sln --configuration Release
cd ../..

# 3. Copy LEAN reference data to lean-data/
mkdir -p lean-data/symbol-properties lean-data/market-hours
cp engine/Lean/Data/symbol-properties/symbol-properties-database.csv lean-data/symbol-properties/
cp engine/Lean/Data/market-hours/market-hours-database.json lean-data/market-hours/

# 4. Create Python environments
python -m venv .venv               # Python 3.14 — data pipeline, FastAPI
py -3.11 -m venv .venv311         # Python 3.11 — LEAN engine only

# 5. Install Python dependencies
.venv/Scripts/activate              # Windows (or source .venv/bin/activate on Linux)
pip install -r requirements.txt

.venv311/Scripts/activate
pip install numpy pandas scipy scikit-learn questdb python-dotenv

# 6. Start native services (no Docker)
# QuestDB: download from questdb.io, run questdb.exe start
# Redis: install Redis or Memurai (Windows), run redis-server

# 7. Set environment variables (.env file)
DHAN_CLIENT_ID=...
DHAN_ACCESS_TOKEN=...
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
OANDA_ACCOUNT_ID=...
OANDA_ACCESS_TOKEN=...
ANTHROPIC_API_KEY=...

# 8. Verify everything works
python setup/verify.py    # Checks: LEAN builds, QuestDB running, Redis running
```

---

## 🔖 .gitmodules — Must Exist at Root

```ini
[submodule "engine/Lean"]
    path = engine/Lean
    url = https://github.com/QuantConnect/Lean.git
    branch = master
```

---

## 🔖 .gitignore — Complete

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
.venv311/
*.egg-info/
dist/
build/
.pytest_cache/

# Environment / secrets
.env
.env.local
*.env

# LEAN outputs (large, generated)
lean-data/
lean-results/
*.zip

# SQLite databases (generated)
*.db
*.sqlite
platform/agents/memory.db

# QuestDB data (generated)
questdb-root/

# Node / Frontend
node_modules/
frontend/.next/
frontend/out/

# OS
.DS_Store
Thumbbs.db

# IDE
.vscode/
.idea/
*.swp

# Logs
*.log
logs/

# Redis
dump.rdb
```

---

*This document is the single source of truth for what this platform is and how it is built.*  
*PLAN.md contains the detailed step-by-step build sequence.*  
*CONTEXT.md contains the history of decisions and corrections.*  
*PROGRESS.md tracks current build status.*
