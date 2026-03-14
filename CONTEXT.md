# 🧠 Full Project Context — Everything an AI Agent or Developer Needs

**Read this before anything else.**  
This document captures the complete history of this project: every conversation, every research decision, every mistake found, every correction made, and every reason behind every choice. If you are an AI agent or developer picking this up fresh, this is your starting point.

---

## Who Built This and Why

**Developer:** Satya (solo developer)  
**Background:** Strong in algorithmic trading for Indian markets (NSE), Spider Multi-Timeframe Wave System, reverse engineering, systems programming. Working with Cline as an AI coding assistant. Uses Claude API as a core component.

**The Origin Problem (First Message):**  
> "I want to develop a new trading system but I keep failing to develop in terms of data fetching and storing and in realtime data live feed in frontend. So for this can you find repo or website repo for trading which can populate realtime data and it has storage — are there any source code for all of these?"

This was the starting point. Not "I want to build X" but "I have tried many times and failed in these specific ways." Understanding the failure pattern was the key to the correct design.

---

## The Exact Failures That Kept Happening

These are direct quotes from the conversation. Read them carefully — they explain every architecture decision.

**Failure 1 — Symbol mapping always breaks when adding a new broker:**
> "Its not only for indian market but for the whole world [...] I fail at adding new broker and realtime data fetching because of security id mismatch and fetching security id of stocks and strikes [...] broker has some data format and lean has other it has to get converted and stored"

This is why `instrument-master/schema.sql` and `symbol-mapper/universal_mapper.py` are Phase 0 components, not Phase 3. Every previous attempt built strategy first and handled symbol mapping as an afterthought. That always fails.

**Failure 2 — Data download crashes and never resumes:**
> "From my experience while downloading historical data I could not download all the data at once. Suppose any market like NSE has nearly 6k-12k stocks [...] when I tried AI was able to download 20 stocks data, that too 1 year or 2 year, then it will try for 40 stocks and it will fail. It does not have proper planning and proper process based on rate limit of different brokers."

This is why the intraday downloader uses an SQLite-backed job queue instead of a simple loop. The queue stores every job's status. If the process dies at job 400, restart picks up at job 401.

**Failure 3 — Frontend live data freezes the UI:**
This emerged from studying broker frontend patterns. React state cannot receive 200 ticks/second. The UI becomes unusable within seconds. This is why the performance architecture (Sub-Phase 7.3) separates hot/medium/cold data into completely different update mechanisms.

**Failure 4 — Fee model doesn't account for SEBI changes:**
The developer noticed actual P&L was different from backtest P&L. SEBI changed STT in October 2024 (options: 0.0625% → 0.1%), changed lot sizes in December 2024, changed weekly expiry rules in November 2024. A backtest running across 2022–2024 with hardcoded fees produces wrong results.

---

## The Complete Conversation History — Key Points

### Session 1: Finding the Right Starting Point

The developer first asked for open-source trading platform repos. After reviewing OpenAlgo, revdog-leanflow, Open Trading Platform (Golang/React), the conversation clarified the real need: not just a data tool, but a complete platform that looks and works like Dhan/Angel One.

**Key finding from session 1:**  
Dhan, Zerodha, Angel One frontend code is NOT open source. But their components are:
- Charts: TradingView Charting Library (they all use this)
- Data grids: AG Grid
- Live data: WebSocket from broker SDK
- Framework: React/TypeScript

**AlgoLoop suggestion:** The developer mentioned AlgoLoop (Capnode/Algoloop on GitHub), a WPF/C# desktop app built on LEAN. We analyzed it and found: it's Windows-only (WPF), cannot run in browser, last commit July 2025, broker config not implemented. We cannot use it directly but we copy its architecture patterns — specifically the LEAN communication pattern (write config.json → subprocess → read result.json) and the UI structure (MarketsViewModel, StrategiesViewModel, BacktestViewModel with tabs for Config/Symbols/Parameters/Holdings/Orders/Trades/Charts).

### Session 2: Symbol Mapper and LEAN Internals

The developer asked specifically about symbol mapping across brokers. Research confirmed every broker uses different IDs:
- Dhan: integer `security_id` (e.g., 49581)
- Zerodha: integer `instrument_token` (e.g., 10742530)
- Upstox: string `NSE_FO|58442`
- Angel One: string `58442`

LEAN uses its own Symbol object with: ticker, security type, market, expiry date, strike, option right.

**Key LEAN internal facts discovered from source code:**
- Prices stored as integers × 10,000 (₹94.00 → 940000)
- Timestamps as milliseconds since midnight
- Data in zip archives per symbol per day: `/Data/equity/india/minute/{symbol}/{YYYYMMDD}_trade.zip`
- India market hours: 9:15–15:30 IST
- LEAN has `Market.India`, `IndiaOrderProperties`, `ZerodhaBrokerageModel` built in
- LEAN CANNOT be imported as Python package — it is C# only. Python algorithms run inside LEAN via Python.NET bridge
- Communication from Python: write config.json → `lean backtest` subprocess → read result JSON

**Optimization algorithms in LEAN:**
- `GridSearchOptimizationStrategy`: exhaustive, tests every combination, one generation, all parallel. Good for small discrete parameter spaces.
- `EulerSearchOptimizationStrategy`: iterative refinement, divides parameter space into 4 segments, zooms into best region, stops when step ≤ minStep. Good for continuous spaces.
- Professional workflow: Grid Search first (see the landscape) → Euler Search (drill into best peak) → Walk Forward Validation

### Session 3: Book Research and Architecture

The developer asked to read textbooks and build the plan based on them. Books studied:

**Primary (architecture decisions):**
1. Narang — *Inside the Black Box* (2024): Gave the 4-component framework
2. Johnson — *Algorithmic Trading & DMA* (2010): Transaction costs, VWAP execution
3. Davey — *Building Winning Algo Trading Systems* (2014): 5-gate validation
4. Jansen — *ML for Algorithmic Trading* (2020): Data pipeline, corporate actions
5. López de Prado — *Advances in Financial ML* (2018): CPCV, HRP, why backtests lie

**Secondary (modern, 2019–2025):**
6. Carver — *Systematic Trading* (2015): Forecast scaling, position sizing
7. Carver — *Advanced Futures Trading Strategies* (2023): 30 tested strategies
8. López de Prado — *ML for Asset Managers* (2020): HRP confirmed
9. López de Prado — *Causal Factor Investing* (2023): Causal alpha design
10. Harris — *Trading and Exchanges* (2002): Order types, microstructure
11. Carver — *Leveraged Trading* (2019): Safe leverage calculation
12. Durenard — *Professional Automated Trading* (2013): OMS lifecycle

### Session 4: Dhan Broker Research

The developer chose Dhan as first broker because it provides historical options OHLCV + Open Interest. This is rare. Most Indian brokers either don't have options history or only provide limited data.

**Dhan rate limits (from official docs, verified):**
- Historical intraday: 20 req/sec (most liberal in industry)
- Option chain: 1 req per 3 seconds
- Order placement: 25 orders/sec, 250 orders/min
- Intraday window: 90 days per request
- Daily data: from stock inception date
- Access tokens expire every 24 hours (SEBI regulation)
- Data API: free if 25 F&O trades/month, else Rs 499/month

### Session 5: SEBI and Data Pipeline Research

**SEBI Changes (2024) — Critical for fee model:**
- Oct 1, 2024: STT on futures 0.0125%→0.02%, options 0.0625%→0.1%
- Nov 20, 2024: Weekly expiries reduced — only Nifty50 (NSE) and Sensex (BSE) remain. BankNifty, FinNifty, MidcapSelect weekly options GONE.
- Dec 24–26, 2024: Nifty lot size 50→25, BankNifty 15→30
- Feb 10, 2025: No calendar spread margin benefit on expiry day
- Apr 1, 2025: Intraday monitoring of position limits begins

**Data download discovery (the biggest practical insight of the entire project):**

The failure mode: loop over 2000 symbols making one API call each. This fails because:
1. 2000 symbols × 20 chunks = 40,000 API calls
2. No retry on failure → crash at symbol 40 → start over
3. Wrong data source for EOD data

The correct approach:
- **EOD data**: Use NSE Bhavcopy — one ZIP file per day = OHLCV for ALL 2000+ stocks. Free, no rate limiting, 10 years in 7 minutes.
- **Intraday data**: SQLite job queue. All jobs created upfront. Status tracked per job. Resumable after any crash.

### Session 6: Charting and Database Research

**Charting decision:**
- TradingView Advanced Charts: Free for public web projects but requires application + approval. NOT for private/internal use. Risk of revocation.
- TradingView Lightweight Charts: Apache 2.0, open source, but NO drawing tools and NO built-in indicators.
- **KLineChart Pro** (Apache 2.0): Full professional drawing tools, built-in indicators, zero dependencies, zero restrictions. This is the decision.

**Database decision:**
- Initial plan: TimescaleDB
- Research finding: QuestDB is 41× faster for OHLCV aggregation (25ms vs 1,021ms), ingests 1.4M rows/second vs TimescaleDB's 145K, was built by ex-low-latency trading engineers specifically for financial data.
- **QuestDB replaces TimescaleDB.**

**Technical indicator decision:**
- Python backend: TA-Lib (C core, BSD license, 150+ indicators, 60+ candlestick patterns, 2-4× faster than pandas-ta)
- Frontend: KLineChart built-in indicators
- Research: pandas-ta maintainer issued warning about unsustainable maintenance load. Use `pandas-ta-classic` (community fork) for notebooks.

### Session 7: Frontend Architecture Research

From studying how broker UIs work (Dhan, Kite, Angel One, Upstox):

**What all Indian broker UIs use:**
- Charts: TradingView Charting Library (they all have agreements with TradingView)
- Order book / positions: AG Grid (the best grid for financial apps)
- Live data: WebSocket from broker SDK → React state
- Framework: React/TypeScript (Bloomberg, J.P. Morgan, all major brokers use this)

**Open source reference projects studied:**
- revdog-leanflow: LEAN + FastAPI + React 18 + Ant Design — closest to our stack
- openalgo-desktop: Tauri (Rust) + React frontend covering all broker operations
- Open Trading Platform (ettec/open-trading-platform): Golang + React with AG Grid, most professional reference architecture
- OpenAlgo (marketcalls): Flask + React + 30+ Indian brokers, unified WebSocket via ZeroMQ, TradingView Lightweight Charts for P&L

**The performance architecture insight (the most important frontend discovery):**

All previous attempts put tick prices in React state. At 200 ticks/second this triggers 200 React renders/second — the UI freezes completely. The correct architecture:
1. WebSocket lives as a singleton class OUTSIDE React
2. Price cells register direct callbacks with the singleton
3. Ticks → callback → `element.textContent = newPrice` (pure DOM, no React)
4. Only slow data (positions, P&L) uses React state (5-second polling via Zustand)

---

## Complete Decisions Log — Every Decision and Its Reason

This is the authoritative decision log. Every decision is here. Do not change these without understanding the research behind them.

### Engine
| Decision | Outcome | Reason |
|----------|---------|--------|
| Trading engine | QuantConnect LEAN | 10+ years production, India + global built-in, open source, Python strategy support |
| LEAN communication | Subprocess (not Python import) | LEAN is C#. Python algorithms run inside LEAN via Python.NET. External communication is via config.json → subprocess → result.json (AlgoLoop pattern). |
| LEAN data format | 10000× integer prices, ms timestamps | Verified from LEAN C# source code. All data writers must apply this. |

### Data
| Decision | Outcome | Reason |
|----------|---------|--------|
| EOD data source | NSE Bhavcopy (not per-symbol API) | 1 file = 2000+ stocks. 10 years in 7 minutes. Free. No rate limiting. Per-symbol API for EOD data is the mistake that causes all downloads to fail at stock 40. |
| Intraday data | Dhan API + SQLite job queue | SQLite makes the downloader resumable. Crash at job 400 → restart → picks up at job 401. Never from scratch. |
| Tick/bar storage | QuestDB | 1.4M rows/sec ingestion, 25ms OHLCV query (vs 1,021ms TimescaleDB). Built by ex-trading engineers. Apache 2.0. |
| Pub/sub | Redis | Live ticks from broker WebSocket → Redis pub/sub → FastAPI WebSocket → multiple frontend clients. Broker credentials stay server-side. |
| Instrument master | SQLite | Symbol maps, lot sizes, download job queue. Fast reads, zero config. |
| Rate limiting | 8 req/sec (Dhan max is 20) | Conservative rate stays safe from IP bans. Token bucket limiter prevents bursts. |

### Strategy
| Decision | Outcome | Reason |
|----------|---------|--------|
| Framework | Narang 4-component | Alpha → Risk → Portfolio → Execution. Previously the plan had no risk model and no portfolio construction model. Added after reading Inside the Black Box. |
| Portfolio model | HRP (RiskParityPortfolioConstructionModel) | López de Prado 2020: HRP beats Markowitz out-of-sample. Does not require inverting unstable covariance matrix. LEAN has this built in. |
| Execution model | VWAP (VolumeWeightedAveragePriceExecutionModel) | Johnson (DMA): VWAP minimises market impact. For thin Indian markets (small-cap F&O), market orders fill far from expected price. |
| Position sizing | Carver forecast framework (−20 to +20) | Prevents over-concentration when 20 correlated NSE stocks signal simultaneously. Without this, the system can be 100% concentrated when all wave signals align. |
| Validation | IS → WFO → Monte Carlo → CPCV → OOS | Davey + López de Prado combined. Monte Carlo (10,000 shuffles) proves real edge vs lucky sequencing. CPCV handles non-IID nature of financial time series. |

### Fee Model
| Decision | Outcome | Reason |
|----------|---------|--------|
| Fee schedule | Versioned by effective date | SEBI changed STT rates Oct 1, 2024. A backtest running across 2022–2024 must use old rates before Oct 2024 and new rates after. Hardcoded fees give wrong P&L. |
| Lot size | Date-aware lookup from lot_size_history | Dec 2024 SEBI changes: Nifty 50→25, BankNifty 15→30. Wrong lot size = wrong margin = wrong position size. |

### Frontend
| Decision | Outcome | Reason |
|----------|---------|--------|
| Chart library | KLineChart Pro | Apache 2.0, drawing tools, indicators, zero restrictions. TradingView Advanced Charts requires application + approval and can be revoked. |
| Data grids | AG Grid Community | MIT license. Handles high-frequency updates in financial tables. Used in production by Bloomberg, major trading platforms. |
| Hot data (ticks) | Direct DOM mutation | NOT React state. 200 ticks/sec via React state = 200 renders/sec = frozen UI. Direct callback → element.textContent bypasses React completely. |
| Medium data (positions) | Zustand + 5-second polling | Updates at human speed. React state appropriate. |
| State management | Zustand (medium) + singleton (hot) | The right tool for each data speed tier. |
| Analytics charts | Recharts | MIT, React-native. For static backtest data (equity curve) React-managed state is fine. |
| Options analytics | D3.js | Custom rendering for IV surface heatmap and payoff diagrams. Neither Recharts nor KLineChart can do these. |

### Technical Indicators
| Decision | Outcome | Reason |
|----------|---------|--------|
| Python indicator library | TA-Lib | C core, BSD license, 150+ indicators, 60+ candlestick patterns. 2-4× faster than pandas-ta. Now has binary wheels (pip install works, no C compile). |
| Frontend indicators | KLineChart built-in | No additional library. For custom indicators computed in Python: push via WebSocket → KLineChart renders. |
| Research/notebooks | pandas-ta-classic | Community-maintained fork after original maintainer warned of sustainability issues. |

### AI Agents
| Decision | Outcome | Reason |
|----------|---------|--------|
| Agent framework | LangGraph | Stateful agents, human-in-the-loop, Ollama-compatible. Stateful is important for multi-step operations like "run backtest → optimize → validate". |
| AI model (online) | Claude API (claude-sonnet) | Best reasoning for financial analysis tasks. |
| AI model (offline) | Qwen via Ollama | RTX 3060 (12GB VRAM). Data stays local. No API costs when offline. |
| Human-in-the-loop | Required before any live order | No agent can place a live order without human confirmation. Agents propose, human approves. This is non-negotiable. |

---

## Mistakes That Were Made and Corrected

These are every mistake that was identified during planning. Any AI agent resuming development must not repeat these.

### Mistake 1: No Risk Model or Portfolio Construction Model (v1)
**What happened:** The original plan had "strategy → execute." No risk management, no position sizing.  
**Why it's wrong:** Without a risk model, a 20% drawdown doesn't stop trading. Without portfolio construction, the system can be 100% in one position.  
**Fix:** Narang's 4-component framework. Alpha → Risk (MaxDrawdown 5%) → HRP Portfolio → VWAP Execution.

### Mistake 2: Zero Slippage Assumption (v1)
**What happened:** Transaction costs were not modelled.  
**Why it's wrong:** Johnson (DMA) shows that underestimating transaction costs by 3–5× is common. A profitable strategy with zero slippage is often unprofitable live.  
**Fix:** DhanFeeModel with exact Dhan fee structure. VolumeShareSlippageModel(0.001). Measured against actual fills in paper trading.

### Mistake 3: Data Pipeline in Phase 2 (v1)
**What happened:** Data pipeline was Phase 2. Strategy development was Phase 1.  
**Why it's wrong:** You cannot run a backtest without data. You cannot test a symbol mapper without data to map.  
**Fix:** Data pipeline moved to Phase 0. It is the very first thing built.

### Mistake 4: TimescaleDB as Tick Database (v2)
**What happened:** TimescaleDB was chosen for tick storage.  
**Why it's wrong:** TimescaleDB ingests 145K rows/sec vs QuestDB's 1.4M. TimescaleDB OHLCV aggregation takes 1,021ms vs QuestDB's 25ms. TimescaleDB is PostgreSQL extension — better for relational workloads, not time-series firehoses.  
**Fix:** QuestDB replaces TimescaleDB.

### Mistake 5: BlackLitterman Portfolio Model (v2)
**What happened:** Plan specified BlackLitterman for portfolio construction.  
**Why it's wrong:** BlackLitterman requires subjective analyst views as input. We have no macro views to input. It would just be empty priors = Markowitz.  
**Fix:** HRP (Hierarchical Risk Parity) via LEAN's built-in RiskParityPortfolioConstructionModel. López de Prado (2020) shows HRP beats Markowitz out-of-sample without requiring analyst views.

### Mistake 6: Per-Symbol API Loop for EOD Data (v1-v3)
**What happened:** Looping over 2000+ symbols making one API call each.  
**Why it's wrong:** 2000 symbols × 20 windows = 40,000 API calls. No retry = crash at symbol 40. No resume = restart from scratch. Wrong tool for EOD data.  
**Fix:** NSE Bhavcopy (one file per day = all stocks). Per-symbol API only for intraday. Intraday has SQLite job queue for resumability.

### Mistake 7: Hardcoded Fee Model (v1-v2)
**What happened:** Fee percentages hardcoded as constants.  
**Why it's wrong:** SEBI changed STT in October 2024. A backtest spanning 2022–2024 with fixed post-2024 fees gives wrong pre-2024 P&L.  
**Fix:** Versioned fee schedules in config/fee_schedules.json with effective_from dates. Backtest engine picks the correct schedule based on trade date.

### Mistake 8: Fixed Lot Sizes (v1-v3)
**What happened:** Lot sizes treated as constants.  
**Why it's wrong:** SEBI changed lot sizes December 2024 (Nifty 50→25, BankNifty 15→30). Wrong lot size = wrong margin = wrong position size.  
**Fix:** lot_size_history table in SQLite with date ranges. Every margin calculation does a date-aware lookup.

### Mistake 9: React State for Live Prices (implied in v1-v3)
**What happened:** Standard pattern of updating React state on each tick.  
**Why it's wrong:** 200 ticks/second = 200 React renders/second = frozen browser UI.  
**Fix:** Singleton WebSocket manager outside React. Direct DOM mutation via callbacks for tick data. React state only for slow/medium data.

### Mistake 10: Walk Forward Validation Alone (v2)
**What happened:** WFO was the only validation after in-sample backtest.  
**Why it's wrong:** WFO still overfits because financial time series is non-IID. Adjacent bars are correlated. Standard cross-validation assumes IID data.  
**Fix:** Added CPCV (Combinatorial Purged Cross-Validation) from López de Prado (2018). Also added Monte Carlo (Davey): shuffle 10,000 times, check 95%+ of shuffles show positive Sharpe.

### Mistake 11: No SEBI Change Monitoring (v1-v3)
**What happened:** Fee model updated manually when remembered.  
**Why it's wrong:** SEBI issued 6+ significant rule changes in 2024 alone. Missing one invalidates backtests and can cause live trading losses.  
**Fix:** sebi_monitor.py runs daily, hashes NSE circulars page, alerts on keyword matches (STT, lot size, margin, weekly expiry, ELM).

### Mistake 12: Vague Frontend Plan (v1-v3)
**What happened:** Frontend was "Phase 7: build React trading terminal" with a list of screens.  
**Why it's wrong:** No order, no architecture decision, no performance constraints identified. This always leads to building components that don't work together.  
**Fix:** 11 sub-phases with strict order. Performance architecture (Sub-Phase 7.3) must be established before any component touches data. Every component classified as hot/medium/cold.

### Mistake 13: AlgoLoop Frontend Re-use Idea
**What happened:** Developer suggested using AlgoLoop's frontend directly.  
**Why it's wrong:** AlgoLoop is C# WPF — Windows-only desktop technology. Cannot run in a browser. Cannot be used for web app.  
**What we take from AlgoLoop:** Only the architecture patterns — LEAN subprocess communication pattern, UI structure (ViewModels, backtest tab layout). We translate these patterns into React, not copy the code.

### Mistake 14: TradingView as Open Source Chart
**What happened:** Plan said "TradingView is free to use."  
**Why it's wrong:** TradingView has multiple products with different licenses. The Lightweight Charts is Apache 2.0 but has NO drawing tools and NO built-in indicators. The Advanced Charts (with indicators + drawing tools) requires application + approval and is only for public web projects — NOT for private/internal use.  
**Fix:** KLineChart Pro as primary (Apache 2.0, full drawing tools, full indicators). TradingView Advanced Charts as optional if free license approved for our public open-source project.

---

## Technical Facts Every Developer Must Know

### LEAN Internals
- LEAN price format: `lean_price = int(raw_price * 10000)`. ₹94.00 → 940000. All data writers must apply this.
- LEAN timestamp format: milliseconds since midnight. 9:15 AM = 33,300,000ms.
- LEAN data files: `/Data/equity/india/minute/{symbol}/{YYYYMMDD}_trade.zip`
- LEAN market hours database: `Data/market-hours/market-hours-database.json` — this controls NSE timezone handling.
- LEAN India classes: `Market.India`, `IndiaOrderProperties` (MIS/CNC/NRML), `ZerodhaBrokerageModel`, `SamcoBrokerageModel`, `ZerodhaFeeModel`.
- Python.NET bridge: Python algorithms run inside LEAN via Python.NET. The Python code does not import LEAN — LEAN imports and runs the Python code.
- LEAN CLI (Docker): Write config.json → `lean backtest` → read result JSON. This is the only communication pattern.

### NSE/BSE Options
- NSE options expiry: always use broker's actual expiry from instrument master. NEVER calculate from calendar. NSE has non-standard expiry dates.
- Options instrument ID format in Dhan: separate security_id for each strike + expiry combination.
- Option chain limit: subscribe only ATM ±10 strikes initially. Full chain = hundreds of instruments, hits WebSocket limits.
- Weekly expiries (post Nov 2024): only Nifty50 on NSE, only Sensex on BSE. BankNifty/FinNifty/MidcapSelect REMOVED.

### Dhan API
- Token validity: 24 hours max (SEBI regulation). Must refresh daily.
- Rate limits: 20 req/sec historical (we use 8), 1 req/3sec option chain, 25 orders/sec.
- Data API: Free if 25 F&O trades/month, else Rs 499/month.
- Intraday window: 90 days per request (use 85 days to be safe).
- Historical intraday depth: up to last 5 years.
- Daily data: from stock inception date, split-adjusted (confirmed in Dhan docs).

### NSE Bhavcopy
- URL pattern: `https://archives.nseindia.com/content/historical/EQUITIES/{YEAR}/{MON}/cm{DD}{MON}{YEAR}bhav.csv.zip`
- Released: daily at ~16:00 IST
- Contains: OHLCV for all listed equities (2000+) in one file
- F&O bhavcopy: separate URL, same pattern, contains futures/options OHLCV + OI
- NSE changed format July 2024: switched to CM-UDiFF format per circular 62424

### QuestDB
- ILP ingestion port: 9009
- PostgreSQL wire port: 8812
- HTTP console: 9000
- Time-based arrays storage — data is always ordered by time, no random writes
- `SAMPLE BY` syntax for OHLCV aggregation from ticks
- Partitioned by DAY for ticks, MONTH for OHLCV

### Margin System (India F&O)
- Total margin = SPAN + Exposure + ELM + Net Option Value
- SPAN files: published by NSCCL daily at ~5 PM, free download
- ELM from Nov 2024: +2% on short index options on expiry day (SEBI change)
- Calendar spread margin benefit: removed from Feb 10, 2025
- Position limits: monitored intraday from Apr 1, 2025 (was EOD before)

---

## Repository File Map — What Every File Is For

```
/
├── PLAN.md              ← Master 4.0 plan — all phases, all decisions
├── CONTEXT.md           ← THIS FILE — complete project history
├── README.md            ← Public-facing overview
├── docker-compose.yml   ← LEAN + QuestDB + Redis + Streamlit (one command)
│
├── config/
│   ├── nse_holidays.json      ← NSE trading calendar (for bdate_range)
│   └── fee_schedules.json     ← Versioned STT rates (pre/post Oct 1, 2024)
│
├── instrument-master/
│   ├── schema.sql             ← SQLite schema: instruments, lot_size_history,
│   │                             download_jobs, regulatory_changes (seeded)
│   ├── instruments.db         ← [GENERATED] SQLite database
│   ├── daily_refresher.py     ← [TO BUILD] 6 AM daily refresh job
│   └── brokers/
│       └── dhan_parser.py     ← [TO BUILD] Parse Dhan CSV instrument master
│
├── data-pipeline/
│   ├── bhavcopy_downloader.py ← [TO BUILD] NSE Bhavcopy async downloader
│   ├── intraday_downloader.py ← [TO BUILD] Dhan API + SQLite job queue
│   ├── lean_writer.py         ← [TO BUILD] QuestDB → LEAN binary format
│   ├── daily_updater.py       ← [TO BUILD] 16:30 IST cron job
│   └── sebi_monitor.py        ← [TO BUILD] SEBI change detector
│
├── symbol-mapper/
│   └── universal_mapper.py   ← [TO BUILD] Bidirectional Dhan ↔ LEAN mapping
│
├── strategies/
│   └── spider-wave/
│       ├── alpha_model.py     ← [TO BUILD] Spider MTF wave → LEAN Insights
│       ├── fee_model.py       ← [TO BUILD] DhanFeeModel (versioned STT)
│       └── main.py            ← [TO BUILD] Full LEAN algorithm
│
├── brokers/
│   ├── dhan/                  ← [Phase 0-2]: WebSocket + REST + token refresh
│   ├── zerodha/               ← [Phase 5]
│   ├── upstox/                ← [Phase 5]
│   ├── angelone/              ← [Phase 5]
│   ├── fyers/                 ← [Phase 5]
│   └── interactive-brokers/   ← [Phase 6]
│
├── agents/                    ← [Phase 3+] LangGraph AI agents
├── api/                       ← [Phase 3] FastAPI backend
│
├── frontend/                  ← [Phase 7] React trading terminal
│   ├── components/
│   │   ├── watchlist/         ← WatchlistPanel (direct DOM mutation)
│   │   ├── chart/             ← KLineChart Pro wrapper
│   │   ├── orders/            ← OrderEntry, OrderBook, Positions (AG Grid)
│   │   ├── backtest/          ← EquityCurve (Recharts), TradesList
│   │   ├── options/           ← OptionChain, IVSurface (D3.js), Payoff
│   │   ├── agents/            ← AI assistant panel
│   │   └── ui/                ← Design system (shadcn components)
│   ├── hooks/
│   │   ├── useWebSocket.ts    ← Singleton WebSocket (NOT React state)
│   │   └── useMarketData.ts   ← Price subscription hook
│   └── pages/                 ← Next.js App Router pages
│
├── tests/                     ← Unit + integration tests
│
└── docs/
    ├── DATA_PIPELINE_COMPLETE.md  ← Full data architecture + rate limits
    ├── CHARTING_RESEARCH.md       ← TV license research + KLineChart decision
    ├── DATABASE_RESEARCH.md       ← QuestDB vs TimescaleDB benchmarks
    ├── BOOKS_REFERENCE.md         ← All 12 books with links
    └── ALGOLOOP_ANALYSIS.md       ← AlgoLoop architecture analysis
```

Files marked `[TO BUILD]` are the Phase 0 deliverables. Files with `[Phase N]` are future phases.

---

## How to Continue Development

### If You Are Starting Phase 0

The exact 5-day start sequence:

**Day 1:** Run `docker compose up -d`. Verify LEAN, QuestDB (localhost:9000), and Redis (localhost:6379) are all healthy. Write a simple Python script that connects to QuestDB via port 8812 (PostgreSQL wire), runs `SELECT * FROM tables()`, and confirms QuestDB is working.

**Day 2:** Build `instrument-master/brokers/dhan_parser.py`. Download the Dhan instrument master CSV from `https://images.dhan.co/api-data/api-scrip-master.csv`. Parse it. Apply `instrument-master/schema.sql` to create the SQLite DB. Load all rows. Print how many were loaded (should be ~50,000+).

**Day 3:** Build `data-pipeline/bhavcopy_downloader.py`. Download one day's bhavcopy (e.g., 2024-12-31). Parse the ZIP. Insert into QuestDB ohlcv_daily table via ILP port 9009. Verify via `SELECT count() FROM ohlcv_daily` at localhost:9000.

**Day 4:** Build `symbol-mapper/universal_mapper.py`. Implement: NIFTY → Dhan security_id lookup → LEAN Symbol construction → back to Dhan security_id. All three steps must work. Print the round-trip result.

**Day 5:** Build `data-pipeline/lean_writer.py`. Query 30 days of NIFTY daily OHLCV from QuestDB. Write it to LEAN's binary zip format at `/data/lean/equity/india/daily/nifty/`. Run a minimal LEAN backtest that reads this file. If LEAN reads it without error, Phase 0 Day 5 is complete.

### If You Are Starting a Later Phase

1. Read `PLAN.md` — find the phase you are in
2. Read `CONTEXT.md` (this file) — understand why decisions were made
3. Read `docs/DATA_PIPELINE_COMPLETE.md` — understand data flow
4. Read the README in the relevant folder (e.g., `agents/README.md` for Phase 3)
5. Check `tests/` — write tests for whatever you are building before or alongside the code

### Things That Will Definitely Go Wrong

**"The symbol mapper isn't finding the instrument"**  
Check: Is the instrument master up to date? Run `daily_refresher.py`. Check: Is the instrument active? Dhan removes expired options from the master daily.

**"The backtest shows different P&L than expected"**  
Check: What date range is the backtest? Check `config/fee_schedules.json` — are the correct STT rates being applied for that date range? Check: Are lot sizes correct for the trade date? Query `lot_size_history` table.

**"The live price feed stops updating"**  
Check: Has the Dhan access token expired? Tokens expire at midnight. Check `brokers/dhan/client.py` token refresh. Check: Is the Redis pub/sub working? Use `redis-cli subscribe trading.ticks.NIFTY` to verify.

**"The frontend watchlist prices freeze during market hours"**  
Check: Are you updating React state on each tick? This must NOT happen. Prices must be updated via direct DOM mutation through the WebSocket singleton callbacks.

**"LEAN says it can't find data for the symbol"**  
Check: Is the data in LEAN format (10000× prices, millisecond timestamps)? Did `lean_writer.py` run for this symbol and date range? Check the LEAN /Data folder structure matches exactly.

**"Option strategy P&L looks too good in backtest"**  
Check: Is the calendar spread margin benefit included? It was removed from Feb 10, 2025. Check: Are you using correct lot sizes? Old lot sizes (Nifty 50 instead of 25) understate margin and make strategies look more capital-efficient.

---

## Context About the Developer

Satya is a solo developer. He is technical and experienced with:
- Pine Script (TradingView strategy development — Spider Wave system)
- Python (algorithmic trading, backtesting, Zerodha Kite API)
- QuantConnect LEAN (attempted backtesting but always failed at broker integration)
- Cline (AI coding assistant, works alongside Claude API)
- Local LLM tooling (Qwen via Ollama on RTX 3060 12GB)
- NSE/BSE F&O markets (actively learning Spider Wave MTF system under a mentor)

He is NOT yet experienced with:
- Production React frontend development (has tried, keeps failing at live data performance)
- Docker/orchestration (basic familiarity, not deep)
- FastAPI (beginner level)

This context matters for how you explain things. Don't over-explain Python basics. Do explain React performance patterns and Docker networking in more detail.

---

## What Success Looks Like at Each Phase

**Phase 0:** `docker compose up` works. `python run_backtest.py` produces a result JSON with equity curve, Sharpe, max drawdown, and trade list. Streamlit dashboard shows the numbers.

**Phase 1:** Spider Wave passes all 5 validation gates. The Monte Carlo test shows 95%+ positive Sharpe across 10,000 shuffles. This proves the strategy has a real edge.

**Phase 2:** 2 weeks of paper trading on Dhan with zero crashes. Measured slippage matches or is within 20% of DhanFeeModel estimates.

**Phase 3:** "Run Spider Wave backtest on NIFTY for 3 years with Euler optimization" typed into Claude Desktop → full backtest results appear within 10 minutes.

**Phase 7:** Full trading terminal at localhost:3000. Watchlist shows live prices without freezing. Order entry works. Backtest results visible. AI assistant answers questions.

**Phase 8:** Someone can clone the repo, run `docker compose up`, and have a working trading platform in under 30 minutes on any Linux machine.

---

*Last updated: March 2026*  
*This document is the institutional memory of the entire project. Keep it updated as new decisions are made.*
