# 🌍 Global AI Trading Platform — Master Development Plan (v4.0)

**Repo:** https://github.com/satyamohapatro1234/Lean  
**Engine:** QuantConnect LEAN (C# core, Python strategy support)  
**Goal:** Production-grade, open-source, AI-native global trading terminal  
**First broker:** Dhan (provides historical options + OI data)  
**Plan version:** 4.0 — Full frontend blueprint + data pipeline corrections + book validation complete

---

## 📚 Book Library — What Each Book Changed in This Plan

Reading the books did not just add knowledge. Each book **changed specific decisions** in the plan. Here is the accounting.

### Narang — *Inside the Black Box* (2024)
The most impactful book. Before reading it, the plan had "strategy → execute". After reading it, the architecture has four distinct, separated components. Every line of the architecture diagram traces back to this book. The key insight: without a Risk Model and Portfolio Construction Model, every strategy is just gambling with no position sizing.

### Barry Johnson — *Algorithmic Trading & DMA* (2010)
Changed the execution model from "place market order" to VWAPExecutionModel. Changed transaction cost estimation from "ignore" to DhanFeeModel with verified slippage. The key finding: most retail traders underestimate transaction costs by 3–5x. A strategy that looks profitable with zero slippage assumption is often unprofitable live.

### Kevin Davey — *Building Winning Algorithmic Trading Systems* (2014)
Changed the validation from "backtest shows profit, deploy it" to a five-gate sequence: In-Sample → Walk Forward Optimization → Monte Carlo → Out-of-Sample → Paper Trade → Live. Every gate must be passed before moving to the next. The Monte Carlo test (10,000 random shuffles) is the most important gate because it answers whether the edge is real or lucky.

### Stefan Jansen — *Machine Learning for Algorithmic Trading* (2020)
Changed data pipeline from "download OHLCV and use it" to a proper pipeline with corporate action adjustment, survivorship bias prevention via MapFiles, and data quality checks before any strategy touches the numbers. A split-unadjusted price series shows false signals that look exactly like real ones.

### Marcos López de Prado — *Advances in Financial Machine Learning* (2018)
Added CPCV (Combinatorial Purged Cross-Validation) to the validation sequence. Changed portfolio model from BlackLitterman to HRP. The key insight: standard walk-forward validation overfits because financial time series is not IID. CPCV is the mathematically correct approach for finance.

### Robert Carver — *Systematic Trading* (2015) and *Advanced Futures Trading Strategies* (2023)
Added the forecast scaling framework (−20 to +20) and instrument diversification multiplier to Spider Wave. Without this, running the strategy on 20 correlated NSE stocks over-concentrates risk. Carver also validated the "trading costs kill most strategies" finding — this confirms why accurate fee models from day one are non-negotiable.

### López de Prado — *Machine Learning for Asset Managers* (2020)
Changed the portfolio construction model from EqualWeighting to HRP (Hierarchical Risk Parity). LEAN has RiskParityPortfolioConstructionModel built in. Out-of-sample, HRP consistently outperforms Markowitz because it does not require inverting an unstable covariance matrix.

### López de Prado — *Causal Factor Investing* (2023)
Added causal thinking to the alpha model design. When Spider Wave fires a signal, the question is now: what is the causal mechanism, not just the correlation? This becomes important in Phase 3 when ML features are added to the alpha model.

### Larry Harris — *Trading and Exchanges* (2002)
Informed the order type design in the execution layer. Market orders, limit orders, stop orders, and IOC orders each have specific use cases in our OMS. The insight: in thin Indian markets (small-cap F&O), market orders often get filled far from expected price. VWAP execution and limit orders with tolerance are safer.

### Carver — *Leveraged Trading* (2019)
Added safe leverage calculation to the position sizing module. The formula target_leverage = target_risk / instrument_vol prevents the system from being over-leveraged in high-volatility periods (like expiry day after SEBI's 2024 changes).

### Larry Harris + Durenard — *Professional Automated Trading* (2013)
Informed the complete OMS (Order Management System) architecture. An order has a lifecycle: Created → Submitted → Pending → Partially Filled → Filled / Rejected / Cancelled. Every state must be tracked and recoverable after system restart.

---

## ⚠️ Complete Corrections Log — What Changed from v1 to v4

### v1 → v2 Corrections
- Added Narang's 4-component framework (was completely missing)
- Added transaction costs (was zero slippage assumption)
- Moved data pipeline to Phase 0 (was Phase 2 — cannot backtest without data)
- Added Streamlit monitoring dashboard in Phase 0

### v2 → v3 Corrections  
- Added 5 new books (Carver × 3, López de Prado × 2)
- Changed portfolio model: BlackLitterman → HRP
- Changed execution model: market order → VWAP
- Added CPCV validation after WFO
- Added Carver position sizing / forecast framework
- Changed database: TimescaleDB → QuestDB (41× faster tick queries)
- Resolved charting decision: KLineChart Pro (Apache 2.0) as primary
- Confirmed TA-Lib as Python indicator library

### v3 → v4 Corrections (This Version)
- Added complete data pipeline with resumable job queue (the download failure problem)
- Added NSE Bhavcopy as primary EOD source (1 file = all stocks, not per-symbol API)
- Added SEBI regulatory change tracking system
- Added versioned fee model (STT changed Oct 2024, lot sizes changed Dec 2024)
- Added margin calculation system (SPAN + ELM + VaR)
- **Added complete frontend development plan — phase by phase from zero**
- Corrected frontend build sequence: backend API must exist before frontend starts
- Added WebSocket architecture for real-time data to frontend
- Added component-by-component build order

---

## 🏗️ Final System Architecture

The platform has four distinct layers. They must be built in order. A frontend without a backend API is useless. A backend without a working data pipeline has nothing to show. A data pipeline without an instrument master cannot map symbols.

```
Layer 1 — Data Foundation
  NSE Bhavcopy → QuestDB (EOD for all 2000+ stocks, 1 file per day)
  Dhan Intraday API → SQLite job queue → QuestDB (rate-limited, resumable)
  Instrument Master → SQLite (symbol maps, lot sizes, fee schedules)
  LEAN /Data folder → populated from QuestDB via writer

Layer 2 — Engine
  LEAN Docker → backtesting engine (subprocess pattern)
  Narang's 4 components: Spider Wave → Risk → HRP → VWAP
  Davey's 5-gate validation: IS → WFO → Monte Carlo → CPCV → OOS

Layer 3 — Backend API
  FastAPI → REST endpoints for all platform functions
  WebSocket manager → real-time tick distribution
  LangGraph agents → AI-assisted analysis

Layer 4 — Frontend Terminal
  React + TypeScript + Next.js → production trading UI
  KLineChart Pro → professional charts with drawing tools
  shadcn/ui + Tailwind → component system
  AG Grid Community → positions / orders / watchlist tables
  WebSocket client → live data from backend
```

---

## 📋 Phase-by-Phase Development Plan

---

## PHASE 0 — Data Foundation and First Backtest
**Duration: Weeks 1–4**  
**Goal: One working backtest with real data, real fees, all 4 components active**

The biggest mistake is building anything visible before the foundation works. Phase 0 has zero frontend. It is entirely about getting data to flow correctly from broker → storage → LEAN engine.

### Step 0.1 — Docker Infrastructure (Day 1–2)

The first thing to build is the Docker environment that every other part of the system depends on. This means writing a single docker-compose.yml that starts LEAN, QuestDB, and Redis together, confirms they can talk to each other, and produces a health check endpoint. Until this exists, nothing else can be tested. The docker-compose must work with a single command: `docker compose up`.

LEAN runs in its official Docker image. QuestDB runs in its official image with port 9000 (HTTP), 9009 (InfluxDB Line Protocol for ingestion), and 8812 (PostgreSQL wire for queries). Redis runs on port 6379. All three must be on the same Docker network so they can reach each other by service name.

### Step 0.2 — Instrument Master (Day 3–5)

Before any data can be stored, the system needs to know what instruments exist and how to refer to them across different broker APIs. The SQLite instrument master database stores: the Dhan security_id, the LEAN Symbol (ticker + market + security type + expiry + strike + option right), lot sizes with their effective date ranges, and exchange segment codes.

The Dhan instrument master CSV is downloaded from the Dhan public URL (no auth required). Every row is parsed into the SQLite schema. The daily refresh job re-downloads this at 6 AM every morning before market open. This catches new listings, delistings, and lot size changes.

The most critical table is lot_size_history because a backtest run on incorrect lot sizes produces incorrect margin requirements and position sizes. This table must store the effective date for every lot size change. The December 2024 SEBI changes (Nifty 50→25, BankNifty 15→30) are already in the initial seed data.

### Step 0.3 — NSE Bhavcopy Downloader (Day 6–8)

The fundamental insight about EOD data: NSE publishes one ZIP file per trading day that contains OHLCV for every listed equity. One file = 2000+ stocks. This is called Bhavcopy. Downloading it correctly means: async HTTP fetch with the NSE archive URL pattern, 0.5 second delay between requests (no rate limiting needed, but politeness), local gzip cache to avoid re-downloading, and parsing the CSV into QuestDB's ohlcv_daily table via the ILP protocol.

For 10 years of EOD data (2014–2024), this means approximately 2,510 requests over about 7 minutes. This is the correct and complete approach for daily data. The F&O Bhavcopy is a separate file with the same structure, containing futures and options OHLCV plus Open Interest.

The downloader must be resumable: it checks the local cache before making any HTTP request. If the file for a given date already exists in the cache, it loads from disk. This means re-running the downloader after an interruption picks up where it stopped.

### Step 0.4 — Dhan Intraday Downloader (Day 9–12)

The intraday downloader is fundamentally different from the Bhavcopy downloader because it is per-symbol, rate-limited, and must cover a large number of requests. The correct architecture is a SQLite-backed job queue.

The queue creation step builds all jobs upfront. For the initial download, the universe is F&O stocks only (approximately 200 symbols). For each symbol, the 5-year period is split into 85-day windows (Dhan's maximum is 90 days, using 85 is safe). This creates approximately 200 × 20 = 4,000 jobs, each stored as a row in the download_jobs SQLite table with status "pending".

The download engine processes these jobs at 8 requests per second (Dhan's max is 20, we use 8 for safety). It uses a token bucket rate limiter so the rate never exceeds this even if some requests complete very quickly. On any HTTP error, the job is retried with exponential backoff. On success, the job is marked "completed" in SQLite and the data is written to QuestDB. 

The critical property: if the process crashes or is killed, restarting it reads the SQLite table and continues from the first "pending" or "failed" job. The download never restarts from scratch.

### Step 0.5 — LEAN Data Writer (Day 13–15)

LEAN does not read QuestDB. It reads data from its own /Data folder, organized as zip archives per symbol per day. The LEAN data writer is a Python script that queries QuestDB for a symbol's OHLCV data and writes it in the LEAN binary format: timestamps as milliseconds since midnight, prices as integer × 10,000.

The writer is run once after the initial download to populate the LEAN /Data folder. After that, the daily updater runs it every evening after the Bhavcopy download to add the new day's bars.

### Step 0.6 — Spider Wave Strategy Minimum Viable Version (Day 16–18)

The strategy file is a Python algorithm that runs inside LEAN. It implements the four Narang components:

The Alpha Model reads price data and emits Insight objects when a wave signal fires. The signal can initially be a simple moving average crossover just to verify the pipeline works. The actual Spider Wave multi-timeframe logic is added incrementally. The Insight carries direction (Up/Down), confidence (maps to Carver's forecast scale), and duration.

The Risk Model uses LEAN's MaximumDrawdownPercentPortfolio at 5% and MaximumDrawdownPercentPerSecurity at 3%. These are LEAN built-in models, zero custom code needed.

The Portfolio Construction Model uses LEAN's RiskParityPortfolioConstructionModel (HRP). This model takes Insights and decides how much of each symbol to hold, using the risk parity approach validated by López de Prado.

The Execution Model uses LEAN's VolumeWeightedAveragePriceExecutionModel. This breaks large orders into smaller child orders to minimize market impact, validated by Johnson's DMA book.

### Step 0.7 — Fee Model (Day 19)

The DhanFeeModel is a Python class that implements LEAN's IFeeModel interface. It computes the complete transaction cost for each trade: brokerage (Rs 20 per executed order for F&O), STT (options: 0.1% of premium on sell side, from Oct 2024 rate), exchange transaction charges (NSE: 0.035% for F&O), SEBI charge (Rs 10 per crore), stamp duty, and GST on brokerage.

The fee schedule is versioned: before October 1, 2024 uses old STT rates; after uses new rates. This is a lookup based on the trade date, not a hardcoded value.

### Step 0.8 — Engine Wrapper + First Backtest (Day 20–22)

The engine wrapper is the Python script that communicates with LEAN. It writes a config.json, launches LEAN as a subprocess, monitors the stdout, and reads the result JSON when complete. This is the AlgoLoop pattern.

The first working backtest milestone: `python run_backtest.py` produces a result JSON with equity curve, Sharpe ratio, max drawdown, trade list, and transaction costs. The numbers do not need to be good. They need to exist and be reproducible.

### Step 0.9 — Data Quality Checks (Day 23–24)

Before claiming Phase 0 complete, run automated data quality checks: no price jumps greater than 20% in one bar, no negative prices, no zero volume on trading days, no gaps on non-holiday trading days, no prices in non-LEAN format. These checks prevent phantom signals in backtests from bad data.

### Step 0.10 — Streamlit Monitoring Dashboard (Day 25–28)

The only UI in Phase 0 is a Streamlit app. It shows: download job progress (total / completed / failed), QuestDB row counts per symbol, last Bhavcopy download date, backtest results (equity curve chart, key metrics table), and LEAN engine status. This is not the real frontend. It is a developer tool to verify the foundation is working.

**Phase 0 Milestone: `docker compose up`, run downloader, run backtest, open Streamlit, see equity curve. Everything works end-to-end.**

---

## PHASE 1 — Strategy Validation
**Duration: Weeks 5–10**  
**Goal: Spider Wave passes all five Davey/López de Prado validation gates**

Phase 1 is entirely about proving the strategy has a real edge before any live money is involved. If it fails any gate, the strategy goes back to alpha redesign. This is not a failure; it is the purpose of Phase 1.

### Step 1.1 — In-Sample Backtest (Week 5)

Run Spider Wave on the F&O universe from 2019 to 2021. Optimize parameters using LEAN's built-in Grid Search and Euler Search optimizers. Record: best Sharpe, best parameter set, equity curve characteristics. The in-sample result is expected to look good because it was optimized on this period. The question is whether it stays good outside this period.

### Step 1.2 — Walk Forward Optimization (Week 6)

Split the 2019–2021 period into rolling windows (e.g., 1 year in-sample, 6 months out-of-sample). Run optimization on each in-sample window, then test on the subsequent out-of-sample window. The WFO Sharpe should be meaningfully lower than the in-sample Sharpe. If it is near zero or negative in most windows, the strategy overfits.

### Step 1.3 — Monte Carlo Robustness Test (Week 7)

The Monte Carlo test is from Davey's book. Take the list of individual trades from the best WFO run. Randomly shuffle the trade order 10,000 times. Compute Sharpe ratio for each shuffle. If the strategy has a real edge, at least 95% of shuffles should show positive Sharpe. If 40% of shuffles show negative Sharpe, the edge is dependent on lucky sequencing, not a real alpha.

This test is not built into LEAN. It is a Python post-processor that reads the trade list from LEAN's result JSON and runs the simulation.

### Step 1.4 — CPCV (Combinatorial Purged Cross-Validation) (Week 8)

CPCV is from López de Prado's 2018 book. It is the mathematically correct cross-validation method for financial time series because it respects the time ordering of data and prevents data leakage from adjacent bars. The CPCV result gives a distribution of strategy performance across all valid test combinations. If the distribution is centered above zero with small variance, the strategy is robust.

### Step 1.5 — Out-of-Sample Test (Week 9)

Run Spider Wave on 2022–2024, which was never touched during optimization. This is the true test. The out-of-sample Sharpe should be within a reasonable range of the WFO Sharpe. A collapse (e.g., WFO Sharpe 0.8, OOS Sharpe −0.3) means the strategy regime-shifted or overfitted despite WFO.

### Step 1.6 — Carver Position Sizing Integration (Week 10)

After validation passes, integrate the Carver forecast framework into the alpha model. Each signal is converted to a forecast value between −20 and +20 based on signal strength. The portfolio construction model uses this forecast to scale position sizes appropriately across instruments. This prevents the system from being 100% in one position when all 20 stocks signal simultaneously.

**Phase 1 Milestone: Strategy passes all 5 gates. Equity curve, trade statistics, robustness metrics documented.**

---

## PHASE 2 — Dhan Live Integration
**Duration: Weeks 11–16**  
**Goal: Live paper trading on Dhan for 2 weeks with zero crashes**

### Step 2.1 — Dhan WebSocket Client

The Dhan WebSocket gives live ticks for up to 1000 instruments per connection. The client must: connect at 9:15 AM, handle reconnection automatically if the connection drops, parse incoming binary tick data into {symbol, timestamp, ltp, bid, ask, volume, oi}, write each tick to QuestDB via ILP, and publish each tick to Redis pub/sub for frontend fan-out.

The Redis pub/sub is what allows multiple frontend browser connections to receive the same live data without each one creating a separate broker WebSocket connection.

### Step 2.2 — Dhan Order API Integration

Implement place_order, modify_order, cancel_order, and get_positions functions wrapping the Dhan REST API. Add the pre-order margin check: before placing any order, call the margin calculation function to verify there is sufficient capital. Log every API call with timestamp, request, and response.

### Step 2.3 — Daily Token Refresh

Dhan access tokens expire every 24 hours by SEBI regulation. The automated refresh uses Playwright to log into the Dhan web portal at 6 AM, complete the TOTP 2FA, extract the new access token, and save it to the environment configuration. If this fails, send an alert and halt trading for the day.

### Step 2.4 — Paper Trading Run

Run Spider Wave in LEAN's live mode connected to Dhan paper trading for 2 weeks. Record: all order submissions and fills, actual fill prices vs expected prices, slippage per trade, connection drops and recovery, P&L vs theoretical backtest P&L. The goal is not profitability; it is measuring reality vs model.

**Phase 2 Milestone: 2 weeks of paper trading with zero crashes. Slippage measurements validated against DhanFeeModel assumptions.**

---

## PHASE 3 — FastAPI Backend + Core Agents
**Duration: Weeks 17–22**  
**Goal: REST API complete, 3 core agents working, Claude Desktop integration**

This phase is the first time the backend is truly built as an API. Until now, everything was scripts. Now it becomes a server.

### Step 3.1 — FastAPI Application Structure

The FastAPI application has these endpoint groups:

The data endpoints serve historical OHLCV from QuestDB with symbol and date range parameters. They also serve the instrument master search so the frontend can find symbols by name.

The backtest endpoints accept strategy parameters and date range, launch a LEAN subprocess, return a job ID, and provide polling endpoints for status and results. Results include the full equity curve as JSON, trade list, and key metrics.

The live trading endpoints show current positions, pending orders, order history, and account balance from Dhan.

The agent endpoints accept natural language queries and return agent responses asynchronously.

The WebSocket endpoint broadcasts live ticks to connected frontend clients. This is the single WebSocket connection the frontend maintains for all live data.

### Step 3.2 — WebSocket Architecture

The WebSocket architecture is the most technically complex part of Phase 3. Understanding it is critical.

When the frontend opens a WebSocket connection to the FastAPI server, it subscribes to a set of symbols. The FastAPI WebSocket manager maintains a mapping from symbol to a set of connected clients. When a new tick arrives from Redis pub/sub, the manager pushes it to all clients subscribed to that symbol.

The key design constraint: the frontend must never connect directly to the broker WebSocket. All broker connections are server-side. The frontend connects only to the FastAPI WebSocket. This keeps broker credentials server-side and allows the server to be the single source of truth.

### Step 3.3 — BacktestOrchestrator Agent

The BacktestOrchestrator is a LangGraph agent that accepts natural language like "run Spider Wave on NIFTY for the last 3 years with Euler optimization" and translates it into a structured backtest request. It submits the request to the LEAN engine wrapper, waits for completion, then formats the results into a readable report with key statistics.

This agent is what powers the natural language backtest interface in the frontend and in Claude Desktop via MCP.

### Step 3.4 — RiskMonitor Agent

The RiskMonitor is a background task that runs every 60 seconds during market hours. It reads current positions from Dhan, computes the live P&L and drawdown, compares against the thresholds (3% alert, 5% hard stop), sends alerts if thresholds are breached, and triggers automatic position liquidation at the 5% hard stop.

The RiskMonitor must be restartable: if it crashes, it resumes monitoring immediately on restart without losing position state.

### Step 3.5 — OptimizerAgent

The OptimizerAgent accepts a strategy name and a parameter space description and runs the LEAN optimizer (Grid Search for small spaces, Euler Search for continuous spaces) and returns a ranked parameter heatmap. It also runs the Monte Carlo test on the best result before reporting.

### Step 3.6 — MCP Server

The MCP server is a FastMCP wrapper around the BacktestOrchestrator, RiskMonitor, and OptimizerAgent. It exposes them as tools that Claude Desktop can call. The MCP server config file is committed to the repo so anyone can add it to their Claude Desktop in one step.

**Phase 3 Milestone: "Run Spider Wave backtest on NIFTY for 3 years with optimization" works from Claude Desktop in under 10 minutes.**

---

## PHASE 4 — Options Intelligence
**Duration: Weeks 23–30**  
**Goal: Full options backtesting, live option chain, StrategyAdvisor agent**

Options trading in India has specific technical complexity: Greeks calculation, IV surface construction, multiple expiries per underlying, and SEBI's changing lot size and margin rules. This phase addresses all of it.

### Step 4.1 — Options Historical Data

Dhan provides historical options OHLCV and Open Interest data. The downloader from Phase 0 needs extension to handle options: each strike+expiry combination is a separate instrument with its own security_id. The instrument master lookup gives the correct security_id for any (underlying, expiry, strike, type) combination.

The historical options data goes back approximately 5 years on Dhan. This covers enough history for backtesting common strategies like iron condors, straddles, and calendar spreads across market regimes.

### Step 4.2 — Live Option Chain

The live option chain fetches all strikes and expiries for an underlying via the Dhan WebSocket. The display updates every 3 seconds (matching Dhan's option chain rate limit). The chain shows: strike price, CE/PE LTP, CE/PE OI, CE/PE OI change, IV, Greeks (Delta, Gamma, Theta, Vega computed via Black-Scholes on the backend).

The option chain data is pushed to the frontend via the existing WebSocket infrastructure. The frontend receives JSON updates keyed by (underlying, expiry) and updates the displayed table in place.

### Step 4.3 — Options Analytics Backend

The backend computes Greeks using the Black-Scholes formula on each tick update. It maintains the IV surface: a matrix of implied volatility indexed by strike and expiry. The IV surface is used by the StrategyAdvisor agent to identify rich/cheap strikes.

The OI analysis module computes put-call ratio, max pain strike, and unusual OI concentration. These are key inputs for options traders and are displayed prominently in the options screen.

### Step 4.4 — WaveSignal and StrategyAdvisor Agents

The WaveSignal agent analyses the Spider MTF wave hierarchy for an underlying and recommends a corresponding options structure. If the wave is in a "Grandmother Up / Mother Up / Son Up" alignment, the agent recommends a bullish debit spread. If waves are mixed, it recommends a neutral iron condor.

The StrategyAdvisor agent takes a directional view ("slightly bullish on NIFTY, low IV environment") and recommends specific strike selection for the appropriate strategy, showing the risk/reward profile and required margin.

**Phase 4 Milestone: Select, analyse, and paper trade an options strategy based on agent recommendations using live Dhan option chain data.**

---

## PHASE 5 — Multiple Brokers
**Duration: Weeks 31–36**  
**Goal: Zerodha, Upstox, Angel One, Fyers all working; 6 more agents**

### Step 5.1 — Broker Abstraction Layer

Before adding brokers, build the abstraction layer. Every broker must implement the same interface: authenticate(), place_order(), modify_order(), cancel_order(), get_positions(), get_holdings(), get_orders(), subscribe_ticks(symbols), get_historical(symbol, interval, from, to). This interface means the strategy engine never knows which broker it is using.

### Step 5.2 — Zerodha Integration

Zerodha's KiteConnect is the most mature broker API in India. The Python SDK (pykiteconnect) has built-in WebSocket with auto-reconnect. Zerodha also offers the basket margin API which is the most accurate pre-order margin check available for free (better than estimating from NSCCL SPAN files).

### Step 5.3 — Upstox Integration

Upstox API is free (no monthly subscription). The WebSocket uses Protobuf encoding which is more efficient than JSON. Upstox is a good choice for users who want to test the system without broker API costs.

### Step 5.4 — Angel One and Fyers

Both provide standard REST + WebSocket APIs with Python SDKs. Angel One provides the SmartAPI with margin calculator. Fyers provides options chain data and historical data similar to Dhan.

### Step 5.5 — Remaining 6 Agents

The NewsAnalyst agent monitors NSE corporate announcements, earnings releases, and macro data for symbols in the current portfolio and generates natural language summaries relevant to open positions.

The OrderAssist agent accepts natural language order descriptions ("buy 2 lots NIFTY 24000 CE expiring next Thursday at market") and translates them into verified order parameters before execution.

The MarketScan agent screens the F&O universe for unusual OI buildup, IV anomalies, and wave signal confluence and produces a daily pre-market briefing.

The PortfolioCoach agent reviews overall portfolio health: correlation between positions, concentration risk, days until expiry for options, and suggests rebalancing actions.

The CapacityAnalyst agent estimates maximum capital that can trade the current strategy before slippage begins to erode returns — the answer for "how large can this strategy scale."

The RegularitoryWatcher agent summarises new SEBI and NSE circulars daily, flags anything affecting open positions or strategy parameters, and updates the fee model if charges changed.

**Phase 5 Milestone: Drop-down broker selector works. All 9 agents operational. Switch from Dhan to Zerodha in one click with zero code change.**

---

## PHASE 6 — Global Markets
**Duration: Weeks 37–44**  
**Goal: Interactive Brokers integration for US equities, Forex, Futures, Crypto**

### Step 6.1 — Interactive Brokers via ib_insync

The ib_insync library provides a clean asyncio wrapper around the IB TWS API. LEAN has a built-in IBBrokerageModel and IB symbol mapper. This means adding IB does not require writing a new backtesting model — only the live trading adapter.

IB gives access to US equities (S&P 500, NASDAQ), US options, European futures (Eurex), Forex (EURUSD, USDINR via NDF), and Crypto. The Carver futures strategies from "Advanced Futures Trading Strategies" apply directly to Eurex futures.

### Step 6.2 — Global Data

LEAN's QuantConnect cloud provides US equity data samples. For full historical data, the IB historical data API can download adjusted US equity prices. For Forex, IB provides free OHLCV.

### Step 6.3 — Multi-Currency Portfolio

Positions in USD, EUR, INR must be converted to a base currency (INR) for the portfolio construction model. The conversion rate is fetched from the same broker that holds the foreign currency position.

**Phase 6 Milestone: Spider Wave or a Carver-style trend strategy runs on SPY (IB) and NIFTY (Dhan) simultaneously with unified risk monitoring.**

---

## PHASE 7 — Full Production Frontend
**Duration: Weeks 45–52**  
**Goal: Professional trading terminal, all panels live, production-ready**

This is the most detailed phase because building a trading terminal frontend is where most projects fail. The failure mode is always the same: trying to build everything at once, or building the UI before the API exists. Phase 7 must be built in strict sub-phase order.

### Understanding the Frontend Development Process

A trading terminal frontend is not a normal web app. It has specific requirements that change the entire approach:

The data volume problem: During market hours, a watchlist of 50 symbols receives 50–200 ticks per second. A naive React implementation re-renders the component tree on every tick. At 200 ticks per second, this is 200 full React renders per second. The UI becomes unusable within seconds. The solution is a performance architecture where ticks never trigger React renders directly.

The state management problem: A trading terminal has three distinct kinds of state: slow state (user preferences, strategy config — changes rarely), medium state (positions, P&L — updates every few seconds), and hot state (live prices, tick data — updates hundreds of times per second). These must be managed separately with completely different update mechanisms.

The layout problem: A trading terminal needs multiple panels visible simultaneously: chart, watchlist, order book, positions, order entry. The layout must be resizable and configurable. Building a fixed layout and then trying to make it resizable later is much harder than starting with a layout manager.

### Sub-Phase 7.1 — Project Setup and Design System (Week 45)

Before writing any component, establish the project foundation. Initialize Next.js 14 with TypeScript. Install and configure Tailwind CSS. Install shadcn/ui and run the CLI to add the base components. Establish the colour theme: dark mode first with a professional trading terminal palette (dark backgrounds, muted text, accent colours for price up/down/neutral).

Create the typography scale: monospace fonts for price display (numbers must align vertically), sans-serif for labels and navigation. Establish the spacing system (8px base grid). Write the design tokens as CSS variables.

Create a Storybook instance. Every UI component gets documented in Storybook with multiple states before it goes into the main application. This prevents visual regressions as the system grows.

The reason this sub-phase exists: trading terminals built without an upfront design system always develop visual inconsistencies. Different panels use different fonts, different colours for the same state, different spacing. This is unprofessional and confusing for traders. Establish the system first, then build everything from it.

### Sub-Phase 7.2 — Layout Shell (Week 45–46)

Build the application shell: the outer container, navigation sidebar, top bar with account summary, and the main panel area. The main panel area uses a flex-grid approach where each panel can be shown or hidden and can be resized by dragging dividers.

The layout shell has no real data yet. It uses hardcoded placeholder data to verify the visual design. At the end of this sub-phase, a designer or experienced trader should look at the layout and say "yes, this looks like a trading terminal."

Reference carefully: Zerodha Kite's three-panel layout (watchlist on left, chart in center, orderbook on right), Dhan's trading layout, and the OpenAlgo desktop app's layout. All these inform what a comfortable trading terminal looks like. Our layout does not need to be identical, but it must feel familiar to someone who trades.

### Sub-Phase 7.3 — Performance Architecture for Live Data (Week 46)

This sub-phase has no visible output. It establishes the internal data flow architecture that everything else depends on.

The architecture is: WebSocket connection lives outside React in a singleton manager class. Ticks arrive at the singleton manager. The manager maintains two things: a ref-based tick store (not React state) that holds the current price for every subscribed symbol, and a pub/sub system that components can subscribe to for specific updates.

For the watchlist (50 symbols updating frequently), the cells use direct DOM mutation: on each tick, the manager calls a callback that the cell registered, which directly updates the DOM element's textContent without going through React at all. This is how professional trading UIs handle high-frequency updates.

For the chart (needs historical data + streaming updates), the chart component is initialized with historical OHLCV from the REST API, then subscribes to 1-minute bar formation events. A new bar is formed when the minute boundary crosses. Only then does the chart update — not on every tick.

For positions and P&L (update every few seconds), these use React state via Zustand, polled from the REST API on a 5-second interval. No WebSocket needed here; polling is appropriate and simpler.

Establish this pattern in writing as a document before any component is built. Every developer working on frontend components must understand which data flow pattern to use for their component's data type.

### Sub-Phase 7.4 — Watchlist Component (Week 47)

The watchlist is the first data-connected component built. It is a vertical list of rows, each showing: symbol name, last traded price, change (rupees), change (%), day high, day low, and a buy/sell button.

The technical requirements: price cells must use the direct DOM mutation pattern from Sub-Phase 7.3 (not React state). Price changes must trigger a colour flash animation (green for up, red for down) that fades out over 500ms. This animation is CSS-only, not React-driven.

Clicking any row on the watchlist loads that symbol into the main chart and updates the order entry panel's symbol field. This is the primary navigation interaction in a trading terminal.

The watchlist data comes from two sources: the initial list loaded from the REST API (last close price, day range), and live ticks from the WebSocket subscription. When the watchlist renders initially, it subscribes to all its symbols in the WebSocket manager.

### Sub-Phase 7.5 — KLineChart Pro Integration (Week 47–48)

The chart is the centerpiece of the terminal. It must show: candlesticks or hollow candles or OHLC bars (user selectable), volume in the sub-pane below the main chart, indicators overlaid (MA, EMA, BOLL on the price chart; MACD, RSI, KDJ in separate sub-panes), all drawing tools (trend lines, Fibonacci retracements, channels, horizontal rays, price notes).

The integration works as follows. KLineChart Pro is imported as an npm package. The chart container div is given a fixed size via CSS. The chart is initialized in a useEffect with the container div as the mount target. Historical OHLCV is loaded from the REST API and fed to the chart's data loader. The chart's built-in datafeed API handles the loading of additional historical data when the user scrolls left.

For live data, a 1-minute bar aggregator runs in the WebSocket manager. When each tick arrives, it determines if the tick belongs to the current open bar or starts a new bar. When the minute boundary crosses, it closes the current bar and opens a new one. The chart's updateData method is called once per minute with the completed bar, and setData is called to update the current forming bar every few seconds.

The Spider Wave signals are displayed as overlay annotations on the chart. When the backend detects a wave signal for the currently displayed symbol, it sends a marker event via WebSocket. The chart renders this as a label above or below the relevant candle.

### Sub-Phase 7.6 — Order Entry Panel (Week 48)

The order entry panel is the most dangerous component in the system. A bug here causes real financial losses. It must be built with defensive design.

The panel shows: symbol (populated from watchlist click), exchange segment, quantity (with lot size calculator showing ₹ value), order type (Market / Limit / SL / SL-M), product type (MIS/NRML/CNC), price (enabled only for limit orders), trigger price (enabled only for SL orders), and a "Calculate Margin" button that calls the backend margin API before showing the trade cost breakdown.

The order flow has confirmation gates. Clicking "Buy" or "Sell" first shows a confirmation modal with all order details and calculated transaction costs. Only after confirmation does the order API call go out. There is no "one-click order" mode by default; it must be explicitly enabled in settings.

Error handling: every API error must produce a visible, specific error message. "Order failed: insufficient margin, need ₹12,340 more" is a good error. "Error 400" is not. The backend must return structured error messages with specific codes.

### Sub-Phase 7.7 — Positions and Orders Panel (Week 49)

The positions panel shows all open positions: symbol, product, quantity, average price, LTP, P&L, change percentage, and a square-off button. The table is implemented with AG Grid Community edition (MIT license). AG Grid handles the cell rendering performance for this type of tabular data far better than any custom implementation.

The P&L column uses the performance architecture from Sub-Phase 7.3: it receives live ticks for the position symbols and updates the P&L cells directly without React re-renders.

The orders panel shows today's orders: order ID, symbol, type, quantity, price, status, and time. It has tabs for pending orders and completed orders. Status updates arrive via the WebSocket order update channel.

### Sub-Phase 7.8 — Backtest Results Viewer (Week 49–50)

The backtest results viewer shows the output of the LEAN engine in a readable form. It has tabs matching the AlgoLoop WPF application's structure: Configuration (what parameters were used), Equity Curve (Recharts line chart of portfolio value over time), Drawdown Chart (Recharts area chart of drawdown percentage), Statistics (Sharpe, Sortino, max drawdown, win rate, profit factor in a clean table), Trades (AG Grid table of all trades with P&L per trade), and Holdings (what positions were held on each day).

The equity curve chart uses Recharts because it is pure React and integrates cleanly with the rest of the React application. Unlike the live price chart (which needs high-frequency updates), the backtest equity curve is static data and React-managed state is perfectly appropriate.

### Sub-Phase 7.9 — Options Chain View (Week 50–51)

The options chain view is a specialized screen for F&O traders. It shows the current option chain for a selected underlying with: all expiry dates in a tab strip, strike prices in a vertical list centered on ATM, CE and PE columns showing LTP, OI, OI change, IV, Delta, and volume for each strike.

The cells use the direct DOM mutation pattern because option chain data updates every 3 seconds across potentially hundreds of cells. The IV surface chart (strike vs expiry vs IV as a heatmap) uses D3.js because it requires custom rendering that neither Recharts nor KLineChart can provide.

The strategy builder section of this view allows the user to click on specific strikes to add them to a multi-leg strategy, shows the combined payoff graph (D3.js), calculates the net premium, margin required, and expected P&L at expiry.

### Sub-Phase 7.10 — AI Assistant Panel (Week 51)

The AI assistant panel is a chat interface connected to the LangGraph agents via the FastAPI backend. It is a floating sidebar that can be shown or hidden.

The panel handles both quick queries ("what is the current wave status on NIFTY") and complex multi-step operations ("run a backtest on Spider Wave for the last 3 years and then optimize the parameters"). For complex operations, it shows a progress indicator while the backend agent is processing.

The panel understands context: if the user is looking at the NIFTY chart when they type "what's the wave status", the backend agent knows to analyse NIFTY specifically. The currently viewed symbol is sent as context with every agent request.

### Sub-Phase 7.11 — Settings and Configuration (Week 52)

Settings covers: broker configuration (which broker to use, API credentials), alert thresholds (drawdown alert level, P&L alert), watchlist management (create, rename, delete watchlists), display preferences (chart type, colour scheme, indicator presets), and AI model selection (Claude API online vs local Qwen via Ollama).

The broker configuration screen is particularly important: it must never show API keys in plaintext. They are always masked. The ability to test a connection before saving prevents misconfigured credentials from disrupting live trading.

**Phase 7 Milestone: Full trading terminal at localhost:3000. All panels live with real data. Buy and sell buttons work on Dhan paper trading. Backtest results visible. AI assistant answering questions about current portfolio.**

---

## PHASE 8 — Open Source Launch
**Duration: Weeks 53–56**  
**Goal: One-command setup, documentation, community**

### Step 8.1 — Docker Compose Production Setup

The production docker-compose.yml brings up all services: LEAN engine, QuestDB, Redis, FastAPI backend, Next.js frontend, Nginx reverse proxy, and Certbot for HTTPS. A single command `docker compose up -d` starts the entire platform on any Linux machine with Docker installed.

Environment variables for secrets are managed via a .env.example template. The README makes it clear where to put API keys and how to run the daily token refresh.

### Step 8.2 — Documentation

The documentation covers four audiences. For the setup user: install guide with prerequisites (Docker, Node.js, Python), configuration guide, broker API setup guide for each supported broker, and troubleshooting FAQ. For the strategy developer: how Spider Wave works, how to add custom indicators, how to modify the alpha model, how LEAN's Python strategy API works. For the contributor: code architecture overview, how to add a new broker, how to add a new agent. For the trader: how to use the watchlist, how to place orders, how to read the backtest results.

### Step 8.3 — Community and Release

Create the GitHub release with a changelog. Set up a Discord server for community support. Record a 10-minute demo video showing the complete flow: download data, run backtest, optimise, validate, paper trade, switch to live. Post on relevant communities.

---

## 📊 Complete Technology Decision Table

| Decision | Choice | Why |
|----------|--------|-----|
| Backtesting engine | QuantConnect LEAN | 10+ years production, India + global built-in, 4-component support |
| Primary EOD data | NSE Bhavcopy | Free, 1 file = all stocks, no per-symbol API calls |
| Intraday data | Dhan API (job queue) | Historical options + OI, resumable SQLite queue |
| Tick storage | QuestDB | 1.4M rows/sec ingestion, 25ms OHLCV queries, financial-first design |
| Pub/sub | Redis | Sub-ms latency, WebSocket fan-out to multiple clients |
| Instrument master | SQLite | Fast reads, zero config, adequate for mapping |
| Python indicator library | TA-Lib | C core, fastest, BSD license, 150+ indicators |
| Frontend framework | React + TypeScript + Next.js | Validated by every major trading platform |
| Main trading chart | KLineChart Pro | Apache 2.0, drawing tools, indicators, zero restrictions |
| Optional chart upgrade | TradingView Advanced Charts | Apply for free license if public project requirement met |
| UI component system | shadcn/ui + Tailwind | Modern, composable, dark mode native |
| Data grids | AG Grid Community | MIT license, handles high-frequency updates |
| Equity curve charts | Recharts | React-native, MIT license, good for static backtest data |
| Options visualisation | D3.js | Custom rendering for IV surface and payoff diagrams |
| State management | Zustand (medium), Direct DOM (hot data) | Correct tool for each data speed |
| WebSocket client | Custom singleton (not React state) | Performance requirement |
| Agent framework | LangGraph | Stateful, human-in-the-loop, Ollama-compatible |
| AI online | Claude API (Sonnet) | Best reasoning for analysis tasks |
| AI offline | Qwen via Ollama | RTX 3060, data stays local |
| Portfolio model | HRP (RiskParityPortfolioConstructionModel) | López de Prado: beats Markowitz out-of-sample |
| Execution model | VWAP (VolumeWeightedAveragePriceExecutionModel) | Johnson: minimises market impact |
| Position sizing | Carver forecast framework | Handles correlated signals correctly |
| Validation | IS + WFO + Monte Carlo + CPCV + OOS | Davey + López de Prado combined |
| Fee model | Versioned DhanFeeModel | Post-Oct 2024 STT changes require versioning |
| Database: historical | QuestDB | Tick/bar storage |
| Database: config | SQLite | Symbol maps, user config, lot sizes, job queue |
| First broker | Dhan | Historical options + OI, reasonable rate limits |

---

## 🚧 Known Hard Problems

| Problem | Solution |
|---------|----------|
| NSE option expiry ≠ calendar | Always use broker's actual expiry from instrument master, never calculate |
| LEAN 10000× price format | Enforced at data writer: `lean_price = int(raw_price * 10000)` |
| Multi-timezone (NSE/NYSE/Crypto) | Always store UTC; LEAN converts via market-hours-database.json |
| Broker token expiry at midnight | Automated 6 AM Playwright refresh job |
| Survivorship bias | LEAN MapFiles track delistings; maintain full historical universe |
| Non-IID financial time series | CPCV not WFO alone for validation |
| Carver signal correlation | Forecast diversification multiplier across instruments |
| React re-render storm from ticks | Direct DOM mutation for hot data; no React state for ticks |
| Chart initialization before data | Load historical REST → initialize chart → subscribe WebSocket |
| Options chain 500+ cells updating | Direct DOM mutation; not React re-renders |
| SEBI rule changes | Daily hash-diff monitor + versioned fee model |
| Lot size changes in backtests | lot_size_history table with date ranges |
| EOD download for 9000 stocks | NSE Bhavcopy (1 file per day = all stocks); never per-symbol API |
| Intraday download for 200 stocks | SQLite job queue, resumable, 8 req/sec rate limiter |

---

## 🔢 What to Build Right Now

The first 5 days in strict order:

Day 1: docker-compose.yml with LEAN + QuestDB + Redis. Run `docker compose up` and confirm all three start and can ping each other.

Day 2: instrument-master/schema.sql and dhan_parser.py. Download the Dhan instrument master CSV. Parse it. Load it into SQLite. Print how many rows were loaded.

Day 3: bhavcopy_downloader.py. Download yesterday's NSE equity bhavcopy. Parse it. Insert it into QuestDB. Query QuestDB and verify 2000+ rows exist.

Day 4: symbol-mapper/universal_mapper.py. Given "NIFTY" as a string, look up the Dhan security_id. Map it to a LEAN Symbol. Map it back. Print both. Confirm they round-trip correctly.

Day 5: data-pipeline/lean_writer.py. Query QuestDB for NIFTY's last 30 days of daily OHLCV. Write it in LEAN zip format to /Data/equity/india/daily/nifty/. Confirm the file is valid by running a minimal LEAN backtest that reads it.

When Day 5 works, the foundation is real and Phase 0 becomes engineering rather than exploration.

---

*Plan version: 4.0*  
*Books synthesised: 12 books + 3 research papers*  
*Key corrections: 15 identified and fixed*  
*Frontend phases: 11 sub-phases with detailed build order*  
*Data pipeline: complete with rate limiting, resumable queue, SEBI tracking*
