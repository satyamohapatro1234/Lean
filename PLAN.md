# 🌍 Global AI Trading Platform — Master Development Plan

**Repo:** https://github.com/satyamohapatro1234/Lean  
**Engine:** QuantConnect LEAN (open-source, battle-tested)  
**Goal:** World's first open-source, AI-native, multi-broker global trading terminal

---

## 🔬 Research Findings

### Is Agentic Framework Integration with LEAN Possible?

**YES — and someone already did it.**

**Found Repo:** [`taylorwilsdon/quantconnect-mcp`](https://github.com/taylorwilsdon/quantconnect-mcp)  
- **Stars:** 85 | **Forks:** 24 | **Latest:** v0.3.5  
- **What it does:** MCP (Model Context Protocol) server for QuantConnect  
- **Natural language commands like:**
  - *"Create a backtest for NIFTY momentum strategy 2023–2024"*
  - *"Deploy to live trading, kill switch if loss > 5%"*
  - *"Run grid search on EMA parameters and show best Sharpe"*
- **Built with:** FastMCP, Python 3.12, Claude/GPT compatible
- **Limitation:** Cloud-only (QuantConnect platform), not local LEAN

**Our approach is MORE powerful:** We integrate agents with LOCAL LEAN engine
so everything runs on your machine — no cloud dependency, no monthly fees,
works with any broker.

---

### How Agentic Integration With LEAN Works

There are **3 valid ways** to integrate agents with LEAN:

```
METHOD 1 — MCP Server (what quantconnect-mcp does, cloud only)
  AI Client (Claude/GPT) ──► MCP Server ──► QuantConnect Cloud API ──► LEAN

METHOD 2 — LEAN REST API + Agent Tools (LOCAL, our approach)
  AI Agent ──► FastAPI wrapper ──► Local LEAN CLI ──► Local LEAN Engine
  
METHOD 3 — Agent INSIDE LEAN Algorithm (most powerful)
  LEAN Python Algorithm ──► calls LLM API ──► gets signal ──► places order
  (Agent IS the trading strategy)
```

**We will implement all 3**, giving the user maximum flexibility.

---

## 🏗️ Full System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GLOBAL AI TRADING PLATFORM                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    REACT FRONTEND (Next.js)                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │Watchlist │ │Option    │ │Strategy  │ │ AI Assistant │   │   │
│  │  │+ Charts  │ │Chain     │ │Builder   │ │ (Chat Panel) │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │Positions │ │Backtest  │ │Portfolio │ │ Spider Wave  │   │   │
│  │  │Holdings  │ │Results   │ │Analytics │ │ Dashboard    │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │ WebSocket + REST                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  FASTAPI BACKEND (Python)                    │   │
│  │                                                              │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │              AGENTIC LAYER (LangGraph)               │    │   │
│  │  │                                                     │    │   │
│  │  │  MarketScan  StrategyAdvisor  RiskMonitor           │    │   │
│  │  │  Agent       Agent            Agent                 │    │   │
│  │  │                                                     │    │   │
│  │  │  WaveSignal  NewsAnalyst      OrderAssist           │    │   │
│  │  │  Agent       Agent            Agent                 │    │   │
│  │  │                                                     │    │   │
│  │  │  BacktestOrchestrator    OptimizerAgent            │    │   │
│  │  │  Agent                   Agent                     │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │                              │                               │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │           LEAN ENGINE WRAPPER (Python)               │    │   │
│  │  │  run_backtest() | run_live() | run_optimization()   │    │   │
│  │  │  get_results()  | stop()     | get_status()         │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │                              │                               │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │            UNIVERSAL SYMBOL MAPPER                   │   │   │
│  │  │  Zerodha | Upstox | Fyers | AngelOne | Dhan | IB    │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  │                              │                               │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │         INSTRUMENT MASTER (SQLite + Daily Refresh)   │   │   │
│  │  │  broker_id ↔ LEAN Symbol mapping for all brokers    │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────────────┐ │
│  │ LEAN ENGINE   │  │  DATA STORAGE  │  │   AI MODELS            │ │
│  │ (Docker)      │  │  TimescaleDB   │  │   Claude API (online)  │ │
│  │               │  │  Redis (live)  │  │   Qwen/Ollama (offline)│ │
│  │  Backtesting  │  │  SQLite        │  │                        │ │
│  │  Live Trading │  │  /Data folder  │  │                        │ │
│  │  Optimization │  │  (LEAN format) │  │                        │ │
│  └───────────────┘  └────────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 The 8 AI Agents

| Agent | Role | Tools it uses |
|-------|------|---------------|
| **MarketScan Agent** | Scans F&O OI, IV, unusual volume — globally | LEAN data, broker WebSocket |
| **StrategyAdvisor Agent** | Converts market view → optimal options structure | Options pricer, Greeks calculator |
| **RiskMonitor Agent** | Watches live positions, fires alerts | LEAN portfolio, broker positions |
| **WaveSignal Agent** | Runs Spider MTF Wave System signals | LEAN algorithm output |
| **NewsAnalyst Agent** | Sentiment analysis on market news | RSS feeds, news APIs |
| **OrderAssist Agent** | Natural language → order parameters | Broker API via LEAN |
| **BacktestOrchestrator Agent** | Designs, runs, interprets backtests | LEAN CLI wrapper |
| **OptimizerAgent** | Grid/Euler search, interprets results | LEAN optimizer |

---

## 📋 Development Phases

### Phase 0 — Foundation (THIS PHASE — Weeks 1–2)
**Goal:** Get LEAN running locally with one broker working end to end

- [ ] Set up repo structure (this plan document)
- [ ] LEAN Docker setup and config
- [ ] Instrument master downloader (Zerodha + Upstox first)
- [ ] Universal SymbolMapper SQLite database
- [ ] Basic FastAPI wrapper around LEAN CLI
- [ ] One working backtest: Spider Wave on NSE (NIFTY 50)
- [ ] Verify data format (milliseconds + 10000x prices)

**Milestone:** Run `python backtest.py --strategy spider-wave --market NSE` and get results

---

### Phase 1 — Broker Integration (Weeks 3–5)
**Goal:** 5 Indian brokers + IB all connected, symbols resolving correctly

- [ ] Zerodha instrument master → SQLite (daily job)
- [ ] Upstox instrument master → SQLite (daily job)
- [ ] Fyers instrument master → SQLite (daily job)
- [ ] Angel One instrument master → SQLite (daily job)
- [ ] Dhan instrument master → SQLite (daily job)
- [ ] Interactive Brokers instrument universe → SQLite
- [ ] Universal SymbolMapper: broker_id ↔ LEAN Symbol (all 5 brokers)
- [ ] Live WebSocket tick ingestion → Redis → LEAN data feed
- [ ] Paper trading test with Upstox (free API)

**Milestone:** `python live.py --broker upstox --mode paper` streams live ticks with correct symbols

---

### Phase 2 — Backtesting & Data Pipeline (Weeks 6–8)
**Goal:** Historical data for any global instrument in LEAN format

- [ ] Historical data downloader (NSE equities via Zerodha/Upstox)
- [ ] Historical data downloader (NSE F&O options and futures)
- [ ] Historical data downloader (Global via IB or Yahoo Finance)
- [ ] Data format converter: broker OHLCV → LEAN zip format
- [ ] Tick → candle aggregation (1min, 5min, 15min, 1h, daily)
- [ ] LEAN backtesting working for NSE equities
- [ ] LEAN backtesting working for NSE options
- [ ] Walk Forward Optimization working

**Milestone:** Full backtest report for Spider Wave 2019–2024 on NSE with Sharpe, drawdown, all stats

---

### Phase 3 — Agentic Layer (Weeks 9–12)
**Goal:** AI agents that can reason about the market and control LEAN

- [ ] FastAPI LEAN wrapper with REST endpoints
- [ ] LangGraph state machine for multi-agent orchestration
- [ ] Claude API integration (online mode)
- [ ] Qwen via Ollama integration (offline mode)
- [ ] BacktestOrchestrator Agent — creates + runs backtests from natural language
- [ ] OptimizerAgent — runs Grid/Euler search, interprets results
- [ ] RiskMonitor Agent — monitors live positions
- [ ] WaveSignal Agent — integrates Spider MTF signals
- [ ] MCP Server (METHOD 1) — Claude Desktop can control trading platform

**Milestone:** Say *"Run a 2-year backtest on Spider Wave for NIFTY with Euler optimization"* → full results appear

---

### Phase 4 — Options Intelligence (Weeks 13–16)
**Goal:** Full options analytics suite

- [ ] Live option chain fetcher (NSE F&O via Upstox/Dhan)
- [ ] Option chain UI (strike, IV, OI, Greeks — Dhan-style)
- [ ] Strategy Builder (payoff graph — long/short straddle, iron condor etc.)
- [ ] Greeks calculator (Delta, Gamma, Theta, Vega, Rho)
- [ ] IV surface chart
- [ ] OI change heatmap
- [ ] StrategyAdvisor Agent — suggests structure based on market view
- [ ] LEAN options backtesting (full options strategy backtest)

**Milestone:** Select iron condor on NIFTY, AI calculates max profit/loss, backtests it 1-year

---

### Phase 5 — Global Markets (Weeks 17–20)
**Goal:** Works with any exchange in the world

- [ ] Interactive Brokers live integration (US, EU, Asia)
- [ ] Forex (FX) trading support via LEAN
- [ ] Crypto (Binance, Coinbase) via LEAN adapters
- [ ] European markets (Eurex futures/options)
- [ ] Market hours database for all global exchanges
- [ ] Currency conversion for multi-currency portfolios
- [ ] Global news feed with sentiment

**Milestone:** Run live strategy on US SPY options and NSE NIFTY simultaneously

---

### Phase 6 — Frontend (Weeks 21–24)
**Goal:** Full production-grade trading terminal UI

- [ ] React + TypeScript + Tailwind setup
- [ ] TradingView Charting Library integration (free for non-commercial)
- [ ] Watchlist with live prices (WebSocket)
- [ ] Option chain table (sortable, color-coded)
- [ ] Strategy builder with payoff graph (D3.js)
- [ ] Positions / Orders / Holdings panels
- [ ] Backtest results dashboard
- [ ] AI chat panel (connected to agents)
- [ ] Spider Wave dashboard
- [ ] Portfolio analytics

**Milestone:** Full trading terminal running at localhost:3000, all panels live

---

### Phase 7 — Open Source Launch
- [ ] Docker Compose one-click setup
- [ ] Documentation site
- [ ] Demo video
- [ ] GitHub release
- [ ] Community Discord

---

## 🔑 Key Technical Decisions

### Why LEAN over building from scratch?
- 10+ years of production-tested engine
- Already has India (NSE/BSE), US, EU, Crypto markets built in
- GridSearch + EulerSearch optimization built in
- Options Greeks, expiry, assignment all handled
- Python algorithm support (write strategies in Python)
- Active community + QuantConnect support

### Why LangGraph over LangChain/CrewAI?
- Stateful agents (critical for trading — agents must remember positions)
- Controllable multi-agent with human-in-the-loop
- Works with Ollama (offline/local LLM, your RTX 3060)
- Most production-ready agentic framework as of 2025

### Why NOT use quantconnect-mcp directly?
- Cloud-only (requires QuantConnect account, paid data)
- No local broker integration (Zerodha, Upstox etc. not supported)
- No offline AI mode
- We build something MORE powerful on top of LOCAL LEAN

### Data Storage Strategy
```
Redis           → live ticks (sub-second, in-memory)
TimescaleDB     → historical tick + candle storage (time-series optimized)
SQLite          → instrument master, symbol mappings, user config
/Data folder    → LEAN zip format files (backtesting)
```

### Symbol Mapping Strategy
```
Daily 6 AM job:
  1. Download instrument master from each broker (CSV/JSON)
  2. Parse and normalize columns
  3. Match rows across brokers on (ticker + expiry + strike + optionRight)
  4. Store unified record in SQLite with all broker IDs
  5. LEAN SymbolMapper reads from SQLite at runtime
```

---

## 🚧 Known Hard Problems (Research Required)

### Problem 1: NSE Option Symbol Expiry Dates
NSE changes expiry dates (e.g., post-COVID holiday adjustments). LEAN's
symbol generator uses calendar-based expiry. Broker actual expiry may differ
by 1–2 days. Solution: Always use the instrument master expiry date, never
calculate from calendar.

### Problem 2: LEAN Price Format (10000x multiplier)
LEAN stores all prices as integers × 10000.
₹94.00 stored as 940000.
Feeding raw prices from broker → all prices will be off by 10000x.
Solution: Always apply `price * 10000` before writing LEAN data files.

### Problem 3: Multiple Time Zones
NSE: Asia/Kolkata (+5:30)
NYSE: America/New_York (-5:00 or -4:00)
LEAN uses UTC internally, converts at algorithm level.
Solution: Always store ticks in UTC, let LEAN handle timezone conversion
via market-hours-database.json entries.

### Problem 4: Option Chain Subscription Limits
Zerodha KiteTicker: max 3000 tokens per WebSocket connection.
A full NIFTY option chain (all strikes, all expiries) = ~2000+ tokens.
Solution: Multiple WebSocket connections, group by expiry.

### Problem 5: Broker Daily Token Expiry
All Indian brokers expire API tokens at midnight.
Solution: Automated 6 AM token refresh job using Playwright TOTP login.

---

## 📁 Repository Structure

```
Lean/                               ← This repo (satyamohapatro1234/Lean)
├── PLAN.md                         ← This file
├── README.md                       ← Project overview
├── requirements.txt                ← Python dependencies
├── docker-compose.yml              ← One-click setup
│
├── instrument-master/
│   ├── daily_refresher.py          ← Downloads all broker instrument files
│   ├── normalizer.py               ← Converts each broker format → unified
│   ├── merger.py                   ← Merges all brokers into SQLite
│   ├── schema.sql                  ← SQLite schema
│   └── brokers/
│       ├── zerodha_parser.py
│       ├── upstox_parser.py
│       ├── fyers_parser.py
│       ├── angelone_parser.py
│       ├── dhan_parser.py
│       └── ib_parser.py
│
├── symbol-mapper/
│   ├── universal_mapper.py         ← ISymbolMapper implementation
│   ├── lean_symbol_builder.py      ← Creates LEAN Symbol objects
│   └── tests/
│
├── data-pipeline/
│   ├── tick_collector.py           ← WebSocket → Redis
│   ├── candle_builder.py           ← Tick → OHLCV aggregation
│   ├── lean_writer.py              ← OHLCV → LEAN zip format
│   ├── historical_downloader.py    ← Pull historical data from brokers
│   └── tests/
│
├── brokers/
│   ├── base_broker.py              ← Abstract broker interface
│   ├── zerodha/
│   │   ├── broker.py               ← Zerodha Kite Connect implementation
│   │   ├── websocket_handler.py
│   │   └── config.example.json
│   ├── upstox/
│   │   ├── broker.py               ← Upstox Uplink V2 implementation
│   │   ├── websocket_handler.py
│   │   └── config.example.json
│   ├── fyers/
│   ├── angelone/
│   ├── dhan/
│   └── interactive-brokers/
│
├── lean-engine/
│   ├── engine_wrapper.py           ← Python wrapper around LEAN CLI
│   ├── backtest_runner.py          ← Runs backtests, captures results
│   ├── live_runner.py              ← Starts/stops live trading
│   ├── optimizer_runner.py         ← Runs optimization jobs
│   └── config/
│       ├── backtest.json           ← LEAN backtest config template
│       ├── live.json               ← LEAN live trading config template
│       └── optimizer.json          ← LEAN optimizer config template
│
├── agents/                         ← LangGraph agentic layer
│   ├── orchestrator.py             ← Main LangGraph state machine
│   ├── market_scan_agent.py
│   ├── strategy_advisor_agent.py
│   ├── risk_monitor_agent.py
│   ├── wave_signal_agent.py
│   ├── news_analyst_agent.py
│   ├── order_assist_agent.py
│   ├── backtest_orchestrator_agent.py
│   ├── optimizer_agent.py
│   └── mcp_server.py               ← MCP server (Claude Desktop compatible)
│
├── strategies/
│   └── spider-wave/
│       ├── main.py                 ← Spider MTF Wave System (LEAN Python algo)
│       ├── config.json             ← Strategy parameters
│       └── README.md
│
├── api/                            ← FastAPI backend
│   ├── main.py                     ← FastAPI app entry point
│   ├── routes/
│   │   ├── backtest.py
│   │   ├── live.py
│   │   ├── positions.py
│   │   ├── orders.py
│   │   ├── instruments.py
│   │   ├── agents.py
│   │   └── market_data.py
│   └── websocket_manager.py        ← WebSocket → Frontend bridge
│
├── frontend/                       ← React trading terminal
│   ├── package.json
│   ├── next.config.js
│   └── src/
│       ├── components/
│       │   ├── Watchlist.tsx
│       │   ├── OptionChain.tsx
│       │   ├── StrategyBuilder.tsx
│       │   ├── TradingChart.tsx
│       │   ├── Positions.tsx
│       │   ├── OrderBook.tsx
│       │   ├── BacktestResults.tsx
│       │   ├── AIAssistant.tsx
│       │   └── SpiderWaveDashboard.tsx
│       └── pages/
│           ├── index.tsx           ← Main terminal
│           └── research.tsx        ← Research/backtest page
│
└── docs/
    ├── LEAN_DATA_FORMAT.md         ← Exact LEAN file format spec
    ├── SYMBOL_MAPPING.md           ← How symbol mapping works
    ├── BROKER_SETUP.md             ← How to configure each broker
    ├── AGENT_ARCHITECTURE.md       ← How agents work
    └── API_REFERENCE.md            ← FastAPI endpoint docs
```

---

## 🎯 What We Build That Nobody Else Has

| Feature | Dhan | Sensibull | OpenAlgo | QuantConnect | **Our Platform** |
|---------|------|-----------|----------|--------------|-----------------|
| Open Source | ❌ | ❌ | ✅ | Partial | ✅ |
| Local LEAN Engine | ❌ | ❌ | ❌ | ❌ | ✅ |
| Multi-broker India | ✅ | ✅ | ✅ | ❌ | ✅ |
| Global Markets (IB) | ❌ | ❌ | ❌ | ✅ | ✅ |
| AI Agents | ❌ | ❌ | ❌ | Partial | ✅ |
| Offline AI (Ollama) | ❌ | ❌ | ❌ | ❌ | ✅ |
| MCP Server | ❌ | ❌ | ❌ | ❌ | ✅ |
| Strategy Backtesting | Limited | ❌ | Limited | ✅ | ✅ |
| Optimization (Grid/Euler) | ❌ | ❌ | ❌ | ✅ | ✅ |
| Option Strategy Builder | ✅ | ✅ | ❌ | ✅ | ✅ |
| Spider Wave System | ❌ | ❌ | ❌ | ❌ | ✅ |
| Self-hosted | ❌ | ❌ | ✅ | ❌ | ✅ |

---

## 🚀 Development Order (What We Build First)

**Right now → Phase 0:**
1. Push this plan to GitHub
2. Build `instrument-master/daily_refresher.py` (Zerodha + Upstox)
3. Build `symbol-mapper/universal_mapper.py`
4. Get first backtest running (Spider Wave on NIFTY)
5. Verify LEAN data format is correct (10000x prices)

We build one thing at a time. No skipping phases.
Each phase has a clear milestone before we move on.

---

*Last updated: March 2026*
*Status: Phase 0 — Foundation*
