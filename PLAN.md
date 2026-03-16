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

**Additional insight applied to the 5-layer agent architecture:**
- Narang's 4 components map directly to agent layers: Alpha Model → Decision Layer / StrategyPool; Risk Model → Monitor Layer / RiskGuard+RiskAnalyst; Portfolio Construction → Analysis Layer / PortfolioRebalancer; Execution → Execution Layer / OrderAssist.
- Adding a Supervisor + Research Layer above these gives the complete 5-layer structure.

### Barry Johnson — *Algorithmic Trading & DMA* (2010)
Changed the execution model from "place market order" to VWAPExecutionModel. Changed transaction cost estimation from "ignore" to DhanFeeModel with verified slippage. The key finding: most retail traders underestimate transaction costs by 3–5x. A strategy that looks profitable with zero slippage assumption is often unprofitable live.

### Kevin Davey — *Building Winning Algorithmic Trading Systems* (2014)
Changed the validation from "backtest shows profit, deploy it" to a five-gate sequence: In-Sample → Walk Forward Optimization → Monte Carlo → Out-of-Sample → Paper Trade → Live. Every gate must be passed before moving to the next. The Monte Carlo test (10,000 random shuffles) is the most important gate because it answers whether the edge is real or lucky.

**Additional insight applied to ValidationPipeline:**
- JournalAgent records every trade decision and outcome, making the "paper trade" gate fully instrumented. Davey's core insight: a journal is the difference between learning from experience and just experiencing. Every signal, regime label, recommendation, decision, and outcome is queryable.

### Stefan Jansen — *Machine Learning for Algorithmic Trading* (2020)
Changed data pipeline from "download OHLCV and use it" to a proper pipeline with corporate action adjustment, survivorship bias prevention via MapFiles, and data quality checks before any strategy touches the numbers. A split-unadjusted price series shows false signals that look exactly like real ones.

**Additional insights applied to FeatureEngineer:**
- Dollar bars: resample by traded volume (e.g. every ₹1 crore traded) instead of clock time. Dollar bars are more stationary and IID than time bars — better inputs for ML models.
- Fractional differentiation (López de Prado method, publicised by Jansen): difference a price series by fraction d < 1.0 to achieve stationarity while preserving pricing memory. Applied to price inputs before any ML model training.
- MDI/MDA feature importance: Mean Decrease Impurity and Mean Decrease Accuracy from random forest, used to prune irrelevant TA features before model fitting. FeatureEngineer runs this and outputs `important_features.json` for each strategy.

### Marcos López de Prado — *Advances in Financial Machine Learning* (2018)
Added CPCV (Combinatorial Purged Cross-Validation) to the validation sequence. Changed portfolio model from BlackLitterman to HRP. The key insight: standard walk-forward validation overfits because financial time series is not IID. CPCV is the mathematically correct approach for finance.

### Robert Carver — *Systematic Trading* (2015) and *Advanced Futures Trading Strategies* (2023)
Added the forecast scaling framework (−20 to +20) and instrument diversification multiplier to Spider Wave. Without this, running the strategy on 20 correlated NSE stocks over-concentrates risk. Carver also validated the "trading costs kill most strategies" finding — this confirms why accurate fee models from day one are non-negotiable.

**Additional insights applied to PortfolioRebalancer and StrategyRouter:**
- Buffered target position: hold target ± 3% deadband before trading. Eliminates ~70% of rebalancing trades with almost no impact on risk-adjusted returns.
- Gradual reweighting: when RegimeDetector changes regime, strategy weights shift 10% per day toward the new target — never an instant hard switch. Prevents whipsaw from noisy regime signals.
- Instrument Diversification Multiplier: when SpiderWaveAgent and a second strategy both signal the same underlying, StrategyRouter scales combined position down (not up).

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

**Additional insights applied to agent time partitioning:**
- Durenard's core principle: each agent class has a fixed latency class. Never mix latency classes in the same process.
- RiskGuard runs event-driven per tick (<200ms), never makes LLM calls. Separate from RiskAnalyst which runs on-demand with full LLM reasoning (seconds to minutes).
- Research agents (MarketScan, NewsAnalyst, RegulatoryWatcher) run in 6–9 AM pre-market batch only. No LLM calls during market hours.
- StrategyRouter runs every 60 seconds during market hours — pure Python, no LLM.
- Heavy batch jobs (ValidationPipeline, FeatureEngineer, OptimizerAgent) run post-market or on-demand only.

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

### v4 → v5 Corrections — Lessons from Step 0.8 First Backtest (2026-03-15)

These were discovered during the first real end-to-end run. Each is a concrete defect found, the fix applied, and where it permanently changes the plan.

#### Correction 1: No Docker → LEAN must be built from source. Architecture diagram updated.

**What happened:** The plan's Layer 2 said "LEAN Docker". Docker is not installed and the project rules say no Docker. The LEAN CLI (`lean backtest`) only runs via Docker — there is no `--no-docker` flag in any version.

**Fix applied:** LEAN engine was cloned to `repos/Lean/` and built from source using `dotnet build`. The Launcher runs as a direct subprocess: `QuantConnect.Lean.Launcher.exe --config=...`. This is the permanent approach for all future backtest runs.

**Plan change:** Replace "LEAN Docker" with "LEAN Launcher (built from source)" in architecture. Every future phase that mentions running a backtest means `QuantConnect.Lean.Launcher.exe`, not `lean backtest`.

#### Correction 2: Python version constraint — LEAN requires Python ≤ 3.11. Document this permanently.

**What happened:** The `.venv` was Python 3.14. LEAN's bundled `pythonnet 2.0.53` calls C-level CPython symbols that were removed in later versions:
- `PyUnicode_AsUnicode` — removed in Python 3.12
- `_PyThreadState_UncheckedGet` — removed in Python 3.13

This caused a hard crash at startup. Three Python installs were attempted (3.14, 3.12) before landing on 3.11.

**Fix applied:** Python 3.11.9 installed. New venv `.venv311` created. `PYTHONNET_PYDLL` env var set to `python311.dll` before launching Launcher. `run_backtest.py` sets this automatically.

**Plan change:** All steps that say "use Python venv" must specify `.venv311` for anything that touches LEAN. The main `.venv` (3.14) is only for data pipeline work (downloaders, tests, API). Add to Step 0.1 setup: install Python 3.11 and create `.venv311` with numpy/pandas/scipy/scikit-learn.

#### Correction 3: Daily data timestamp format bug — LEAN requires `YYYYMMDD 00:00`, not bare `YYYYMMDD`.

**What happened:** `bhavcopy_downloader.py` wrote dates as bare integer `YYYYMMDD` (e.g., `20220103`). LEAN's `TradeBar.Reader()` calls `DateTime.Parse()` which rejects this format. All 3313 existing zip files produced `System.FormatException` errors. The backtest ran but loaded zero bars for all symbols.

**Fix applied:**
1. `bhavcopy_downloader.py` `append_to_staging()` now writes `YYYYMMDD 00:00` format.
2. All 3313 existing `.zip` files in `lean-data/equity/india/daily/` were rewritten.
3. All 3313 staging CSVs in `lean-data/_bhavcopy_staging/` were rewritten.

**Plan change:** Add to Step 0.5 (LEAN Data Writer) definition: "All timestamps in daily CSV files must be `YYYYMMDD 00:00` format. Minute files must use milliseconds-since-midnight integer. These are different formats and must not be mixed up." Add a test: `test_lean_format.py::test_daily_timestamp_format` that reads a real zip and asserts ` 00:00` is present.

#### Correction 4: LEAN needs its own reference files inside `data-folder`. Must be seeded at setup.

**What happened:** LEAN expects `symbol-properties-database.csv` and `market-hours-database.json` (and later `map_files/`, `factor_files/`) relative to the configured `data-folder`. We set `data-folder` to `lean-data/` which only had price data. LEAN crashed immediately with `FileNotFoundException`.

**Fix applied:** Copied `symbol-properties-database.csv` and `market-hours-database.json` from `repos/Lean/Data/` into `lean-data/`. This is now a one-time setup step.

**Plan change:** Add to Step 0.1 setup sequence (after LEAN build): copy LEAN static reference data to `lean-data/`. Specifically:
- `repos/Lean/Data/symbol-properties/symbol-properties-database.csv` → `lean-data/symbol-properties/`
- `repos/Lean/Data/market-hours/market-hours-database.json` → `lean-data/market-hours/`

When `lean_writer.py` or any future step adds new data types (futures, options), also ensure the corresponding reference files are present.

#### Correction 5: Phase 0 strategy limitations — not bugs, but must be tracked for Phase 1

**Observed results (2022-01-03 → 2024-12-31, 5 Nifty50 stocks, daily resolution):**
- Sharpe: −0.052 | MaxDD: 18.6% | Net Profit: 0.14% | Orders: 226

**Root causes (all by design at Phase 0, all fixed in Phase 1):**

| Issue | Fix in |
|---|---|
| `Resolution.Daily` instead of minute data — VWAP execution model broken on daily bars | Step 1.1 — switch to minute data after intraday pipeline proven |
| Only 5 stocks, all Nifty50 large-caps (highly correlated) | Step 1.1 — expand to full F&O universe (210 symbols) |
| `MaximumDrawdownPercentPortfolio(0.05)` fires on normal noise, forces re-entry at worse price | Step 1.3/1.4 — tune via Monte Carlo and CPCV |
| `Insufficient buying power` margin rejections (seen in log) — HRP over-allocates for margin account | Phase 2.1 — pre-margin check before sizing; fix margin model assumption |
| SMA 10/30 crossover has eroded edge, especially 2022–2024 choppy/bull regimes | Step 1.6 — Carver forecast scaling, continuous signal −20/+20 |
| `DefaultBrokerageModel` does not match Dhan's actual margin rules | Phase 2.1 — implement `DhanBrokerageModel` |

#### Correction 6: test infrastructure split — downloader tests need questdb, LEAN tests need .venv311

**What happened:** `questdb==1.1.0` fails to build on Python 3.14 (Cython `.pxi` file missing). Tests that import downloader modules cannot even be collected. Also, `python-dotenv` missing from `.venv` breaks all `brokers/dhan/` test collection.

**Fix applied (partial):** Tests are run with `--ignore` on the broken files for now.

**Fix planned:**
- Step 0.9 — install `python-dotenv` into `.venv` permanently. Add to `requirements.txt`.
- Phase 2.1 — fix `questdb` install: either pin to a version that builds on 3.14, or run downloader tests exclusively via `.venv311` where questdb builds cleanly.
- Add `conftest.py` pytest markers: `@pytest.mark.requires_questdb`, `@pytest.mark.requires_lean` to separate test sets cleanly.

---

### v5 → v6 Corrections — Agent Architecture Research (Cross-referencing all 12 books)

These corrections came from systematically cross-referencing the 12-book library against the original 9-flat-agent plan. Each gap traced to a specific book.

#### Correction 1: No separation between agent layers (Narang gap)
The original plan had 9 flat agents with no layer ownership. **Fix:** 5-layer architecture (Research, Analysis, Decision, Execution, Monitor). Narang's 4 components map to layers 3–5. Research layer is new (pre-market intelligence gathering). Agents now know which layer they belong to and which latency class they must meet.

#### Correction 2: No automated validation pipeline (Davey gap)
The original plan had ValidationPipeline as 5 manual steps. **Fix:** ValidationPipeline agent runs all 5 gates in one call and returns a pass/fail verdict. JournalAgent records every trade decision for the "paper trade" gate. Manual steps eliminated.

#### Correction 3: No feature engineering for ML strategies (Jansen gap)
The original plan used raw OHLCV for ML. **Fix:** FeatureEngineer agent converts to dollar bars, applies fractional differentiation, runs MDI/MDA importance filtering before any ML model training.

#### Correction 4: RiskMonitor conflated 3 different latency classes (Harris/Durenard gap)
The original RiskMonitor did: (a) event-driven tick monitoring, (b) periodic P&L reporting, (c) deep risk analysis. These have latency requirements of <200ms, 60s, and minutes respectively — they cannot be in the same process. **Fix:** Split into RiskGuard (event-driven, no LLM, <200ms) and RiskAnalyst (on-demand, LLM, deep analysis).

#### Correction 5: No multi-strategy switching or regime detection (Narang/Carver gap)
The original plan had one strategy (SpiderWave) with no market condition switching. **Fix:** RegimeDetector (HMM on Nifty50 + VIX), StrategyRegistry (SQLite), StrategyRouter (Carver gradual reweighting). Capital shifts between strategies proportional to regime fit × rolling Sharpe.

#### Correction 6: No portfolio rebalancing with tax awareness (Carver/India tax gap)
The original plan had PortfolioCoach as both advisor and rebalancer, with no tax logic. **Fix:** Split into PortfolioRebalancer (pure algorithm: Carver buffer + CPPI + vol targeting + India LTCG/STCG tax gate — produces a proposal table) and PortfolioCoach (LLM explains the proposal). RebalancerAgent never executes; OrderAssist does after human confirmation.

#### Correction 7: No Supervisor / single entry point (LangGraph gap)
The original MCP server exposed 3 separate tools. **Fix:** Single `trading_system` MCP tool. Supervisor routes every request internally, masking the 19-agent complexity from the user.

**Result: Agent count 9 flat → 19 in 5 layers. Agent Architecture section added to PLAN.md above Phase 3.**

---

## 🏗️ Final System Architecture

The platform has four distinct layers. They must be built in order. A frontend without a backend API is useless. A backend without a working data pipeline has nothing to show. A data pipeline without an instrument master cannot map symbols.

```
Layer 1 — Data Foundation
  NSE Bhavcopy → QuestDB (EOD for all 2000+ stocks, 1 file per day)
  Dhan Intraday API → SQLite job queue → QuestDB (rate-limited, resumable)
  Instrument Master → SQLite (symbol maps, lot sizes, fee schedules, rebalance journal)
  LEAN /Data folder → populated from QuestDB via writer

Layer 2 — Engine (NO Docker — runs natively)
  LEAN Launcher → repos/Lean/Launcher/bin/Release/QuantConnect.Lean.Launcher.exe
  Python runtime → .venv311 (Python 3.11) — pythonnet 2.0.53 requires Python <= 3.11
  Narang's 4 components: StrategyPool → Risk → HRP → VWAP
  Davey's 5-gate validation: IS → WFO → Monte Carlo → CPCV → OOS
  Multi-strategy: SpiderWave + MeanReversion + Momentum + OptionsIncome (pluggable)
  RegimeDetector → StrategyRouter → capital allocated per-regime (Carver gradual reweighting)

Layer 3 — Backend API + Agent System
  FastAPI → REST endpoints for all platform functions
  WebSocket manager → real-time tick distribution
  LangGraph agent system → Supervisor + 19 specialised agents in 5 layers
  Agent schedule: research 6–9 AM | analysis nightly | NO LLM calls during market hours
  Memory: SQLite checkpointer (thread + session + long-term + team shared state)
  MCP server → Claude Desktop integration (single "trading_system" tool via Supervisor)

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

### Step 0.1 — Local Environment Setup (Day 1–2)

⚠️ **No Docker** — all services run natively. See `LOCAL_SETUP.md` for step-by-step commands.

The environment setup has these concrete deliverables:

**Services:** QuestDB via `questdb.exe start` (ports 9000/9009/8812), Redis via WSL2 `redis-server` or Memurai (port 6379), LEAN Launcher built from source (no Docker — see below).

**Python versions — two are required:**
- `.venv` (Python 3.14) — for data pipeline (downloaders, FastAPI, agents, tests that don't touch LEAN)
- `.venv311` (Python 3.11) — **mandatory for anything that runs LEAN**. LEAN's bundled `pythonnet 2.0.53` requires Python ≤ 3.11. Python 3.12 removed `PyUnicode_AsUnicode`; Python 3.13 removed `_PyThreadState_UncheckedGet`. Both cause hard crashes at LEAN startup. Install Python 3.11.x separately and create `.venv311` with: `py -3.11 -m venv .venv311` then `pip install numpy pandas scipy scikit-learn`.

**LEAN build (one-time):**
```
cd repos/Lean
dotnet build QuantConnect.Lean.sln --configuration Release
```
Launcher outputs to `repos/Lean/Launcher/bin/Release/QuantConnect.Lean.Launcher.exe`.

**LEAN reference data (one-time, copy after build):**
LEAN requires static reference files relative to `data-folder`. After building, copy:
```
repos/Lean/Data/symbol-properties/symbol-properties-database.csv  →  lean-data/symbol-properties/
repos/Lean/Data/market-hours/market-hours-database.json            →  lean-data/market-hours/
```
Without these, LEAN crashes immediately with `FileNotFoundException` even before loading any price data.

**`python-dotenv` in `.venv`:** Add `python-dotenv` to `requirements.txt` and install it in `.venv`. Absence of this package causes `brokers/dhan/` module imports to fail, breaking all dhan-related tests at collection time.

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

The queue creation step builds all jobs upfront from mapped NSE EQ underlyings (derived from FnO contracts), not from every derivative contract row. For each underlying, the 5-year period is split into 75-day windows (conservative safety below Dhan's 90-day limit). In current runs this produces roughly 6,000+ jobs for the mapped universe.

The download engine uses a shared token bucket capped at 8 requests per second total (Dhan max is 20, we stay at 8 for safety). It runs with parallel workers so network latency is hidden while still respecting the 8 req/sec cap. On retryable API errors, the job uses bounded exponential backoff. On auth expiry (DH-901), the run stops early to avoid burning the whole queue. On success, the job is marked completed and data is written to QuestDB.

The critical property: if the process crashes or is killed, restarting it recovers in-progress jobs and resumes from queue state. Failed jobs are retried in later runs without restarting from scratch.

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

The engine wrapper is `trading-platform/run_backtest.py`. It has three functions:
- `build_lean_config()` — writes `lean-results/lean-config.json` with all required LEAN keys
- `run_backtest()` — launches `repos/Lean/Launcher/bin/Release/QuantConnect.Lean.Launcher.exe` as subprocess with `PYTHONNET_PYDLL` env var set to `python311.dll`
- `parse_results()` — reads `lean-results/SpiderWaveAlgorithm.json`, returns sharpe/drawdown/return/trades

**Critical implementation notes (from first run):**
- Set `PYTHONNET_PYDLL=C:\...\Python311\python311.dll` in subprocess env — without this pythonnet cannot locate the runtime
- LEAN result JSON uses lowercase keys: `statistics`, `charts` (not `Statistics`, `Charts`)
- Statistics use key `Net Profit` (not `Total Net Profit`) and `Total Orders` (not `Total Trades`)
- `python-venv` config key must point to `.venv311`, not `.venv`
- `data-folder` must contain `symbol-properties/` and `market-hours/` subdirs (see Step 0.1)

The first working backtest milestone: `python run_backtest.py` produces a result JSON with Sharpe ratio, max drawdown, net profit, and total orders. The numbers do not need to be good. They need to exist and be reproducible.

**Phase 0 result recorded (2022-01-03 → 2024-12-31, 5 Nifty50 stocks, `Resolution.Daily`):**
Sharpe −0.052 | MaxDD 18.6% | Net Profit 0.14% | Orders 226. Poor by design — daily data, SMA crossover, correlated universe. All fixed in Phase 1.

### Step 0.9 — Data Quality Checks (Day 23–24)

Before claiming Phase 0 complete, run automated data quality checks: no price jumps greater than 20% in one bar, no negative prices, no zero volume on trading days, no gaps on non-holiday trading days, no prices in non-LEAN format. These checks prevent phantom signals in backtests from bad data.

### Step 0.10 — Streamlit Monitoring Dashboard (Day 25–28)

The only UI in Phase 0 is a Streamlit app. It shows: download job progress (total / completed / failed), QuestDB row counts per symbol, last Bhavcopy download date, backtest results (equity curve chart, key metrics table), and LEAN engine status. This is not the real frontend. It is a developer tool to verify the foundation is working.

**Phase 0 Milestone: start native local services (QuestDB + Redis + LEAN launcher), run downloader, run backtest, open Streamlit, see equity curve. Everything works end-to-end.**

---

## PHASE 1 — Strategy Validation
**Duration: Weeks 5–10**  
**Goal: Spider Wave passes all five Davey/López de Prado validation gates**

Phase 1 is entirely about proving the strategy has a real edge before any live money is involved. If it fails any gate, the strategy goes back to alpha redesign. This is not a failure; it is the purpose of Phase 1.

### Step 1.1 — In-Sample Backtest (Week 5)

> **⚠️ Phase 0 problems this step fixes:**
> - **`Resolution.Daily` broke the VWAP execution model.** Phase 0 ran on daily bars because only Bhavcopy (EOD) data existed. Intraday data (Step 0.4) is now available. Switch `main.py` to `Resolution.Minute`. VWAP execution becomes functional automatically — it requires sub-daily bars to compute the weighted average.
> - **Only 5 correlated Nifty50 stocks** produced an undiversified portfolio and inflated drawdown. Expand the universe to the full F&O list (≈210 symbols) using the instrument master built in Step 0.2.

Run Spider Wave on the F&O universe from 2019 to 2021. Optimize parameters using LEAN's built-in Grid Search and Euler Search optimizers. Record: best Sharpe, best parameter set, equity curve characteristics. The in-sample result is expected to look good because it was optimized on this period. The question is whether it stays good outside this period.

**Checklist before running Step 1.1:**
- [ ] `main.py` line 66: `Resolution.Daily` → `Resolution.Minute`
- [ ] Universe expanded to full F&O list from instrument master
- [ ] Intraday LEAN data files present in `lean-data/equity/india/minute/`

### Step 1.2 — Walk Forward Optimization (Week 6)

> **⚠️ Phase 0 problem this step fixes:**
> - **Wrong regime 2022–2024 for trend-following.** Phase 0 backtested 2022–2024 directly (choppy/bull regime — worst possible for SMA crossover trend-following). WFO discovers robust parameter ranges by testing across multiple sub-periods including 2019–2021 (better trending regimes). Track which parameter sets survive regime changes.

Split the 2019–2021 period into rolling windows (e.g., 1 year in-sample, 6 months out-of-sample). Run optimization on each in-sample window, then test on the subsequent out-of-sample window. The WFO Sharpe should be meaningfully lower than the in-sample Sharpe. If it is near zero or negative in most windows, the strategy overfits.

### Step 1.3 — Monte Carlo Robustness Test (Week 7)

> **⚠️ Phase 0 problem this step fixes:**
> - **`MaximumDrawdownPercentPortfolio(0.05)` fired on normal noise.** The 5% portfolio drawdown limit was too tight for Phase 0's undiversified, daily-resolution strategy — it triggered frequently, forced premature exits, and re-entered at worse prices. Monte Carlo over 10,000 trade shuffles reveals the true drawdown distribution. Use the 95th-percentile max drawdown from Monte Carlo to set a realistic risk limit rather than an arbitrary 5%.

The Monte Carlo test is from Davey's book. Take the list of individual trades from the best WFO run. Randomly shuffle the trade order 10,000 times. Compute Sharpe ratio for each shuffle. If the strategy has a real edge, at least 95% of shuffles should show positive Sharpe. If 40% of shuffles show negative Sharpe, the edge is dependent on lucky sequencing, not a real alpha.

This test is not built into LEAN. It is a Python post-processor that reads the trade list from LEAN's result JSON and runs the simulation.

### Step 1.4 — CPCV (Combinatorial Purged Cross-Validation) (Week 8)

> **⚠️ Phase 0 problem this step fixes (continued from Step 1.3):**
> - **Risk parameters tuned on a single period.** CPCV generates many non-overlapping test paths simultaneously. Use the CPCV drawdown distribution (not just Monte Carlo) to confirm the final `MaximumDrawdownPercentPortfolio` setting is grounded in statistical reality across all valid time-period combinations, not just a single backtest run.

CPCV is from López de Prado's 2018 book. It is the mathematically correct cross-validation method for financial time series because it respects the time ordering of data and prevents data leakage from adjacent bars. The CPCV result gives a distribution of strategy performance across all valid test combinations. If the distribution is centered above zero with small variance, the strategy is robust.

### Step 1.5 — Out-of-Sample Test (Week 9)

> **⚠️ Phase 0 problem this step confirms or rejects:**
> - **2022–2024 was the phase 0 test period and produced Sharpe −0.052.** That result is now the baseline to beat. After WFO + Monte Carlo + CPCV, re-run on 2022–2024 with minute resolution and full F&O universe. If OOS Sharpe is still near zero: the SMA crossover has no edge in this regime and the alpha model must be redesigned before Step 1.6. If OOS Sharpe improves meaningfully: the poor Phase 0 result was caused by daily data + small universe, not a broken alpha.

Run Spider Wave on 2022–2024, which was never touched during optimization. This is the true test. The out-of-sample Sharpe should be within a reasonable range of the WFO Sharpe. A collapse (e.g., WFO Sharpe 0.8, OOS Sharpe −0.3) means the strategy regime-shifted or overfitted despite WFO.

### Step 1.6 — Carver Position Sizing Integration (Week 10)

> **⚠️ Phase 0 problem this step fixes:**
> - **SMA 10/30 crossover is binary (fully in or fully out).** A signal either fires or does not — there is no gradation of conviction. In choppy 2022–2024 markets this caused whipsawing: the strategy entered at full size, got stopped out, then re-entered. Carver's forecast framework replaces the binary signal with a continuous value −20/+20 based on signal strength. Weak signals produce small positions; strong signals produce larger ones. This is what makes the system survive mixed regimes.
> - **HRP over-allocated in Phase 0**, causing `Insufficient buying power` margin rejections in the LEAN log when all 5 correlated stocks triggered simultaneously at full size. Carver's instrument diversification multiplier (IDM) applied per symbol caps the combined position weight, preventing over-allocation.

After validation passes, integrate the Carver forecast framework into the alpha model. Each signal is converted to a forecast value between −20 and +20 based on signal strength. The portfolio construction model uses this forecast to scale position sizes appropriately across instruments. This prevents the system from being 100% in one position when all 20 stocks signal simultaneously.

**Phase 1 Milestone: Strategy passes all 5 gates. Equity curve, trade statistics, robustness metrics documented.**

---

## PHASE 2 — Dhan Live Integration
**Duration: Weeks 11–16**  
**Goal: Live paper trading on Dhan for 2 weeks with zero crashes**

### Step 2.1 — Dhan WebSocket Client

> **⚠️ Phase 0 problem this step fixes:**
> - **`DefaultBrokerageModel` does not match Dhan's margin rules.** Phase 0 used LEAN's default brokerage model which assumes exchange-standard SPAN margin. Dhan applies additional exposure margin and intraday leverage rules on top. This caused `Insufficient buying power` rejections even when capital was theoretically sufficient. This step implements `DhanBrokerageModel` (`brokers/dhan/brokerage_model.py`) with a real pre-margin check via Dhan's margin API before any order is sized. The pre-margin check queries Dhan's `/v2/margincalculator` endpoint with the proposed order and confirms sufficient balance before `run_backtest.py` or the live engine submits the order.

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

## 🤖 Agent Architecture — Complete Design

### Why this architecture (vs the original 9-agent flat list)

The original plan had 9 agents as an unstructured flat list called independently. Three problems:

1. **No routing** — you had to know which agent to call. The Supervisor solves this.
2. **No inter-agent data flow** — MarketScan findings never reached WaveSignal. Memory solves this.
3. **No strategy switching** — SpiderWave was hardcoded. RegimeDetector + StrategyRouter solves this.
4. **No long-term portfolio handling** — algo trading and long-term investing are fundamentally different problems. PortfolioRebalancer solves this.

Sources: Narang (ensemble alpha models), Davey (trading journal, automated validation), Jansen (feature engineering), López de Prado (causal validation), Carver (buffered rebalancing, volatility targeting), Harris + Durenard (OMS lifecycle, priority queues).

---

### The 19-Agent System

```
User / Claude Desktop / Frontend Chat
              │
         SUPERVISOR  (single entry point — reads request, routes to correct agent)
              │
  ┌───────────┼───────────────────────────────────────────────┐
  │           │                                               │
RESEARCH   ANALYSIS            DECISION           EXECUTION   MONITOR
LAYER      LAYER               LAYER              LAYER       LAYER
─────────  ──────────────────  ─────────────────  ─────────── ────────────
MarketScan  RegimeDetector      StrategyRouter     OrderAssist RiskGuard
NewsAnalyst FeatureEngineer     StrategyRegistry   JournalAgent RiskAnalyst
Regulatory  ValidationPipeline  SpiderWaveAgent
Watcher     CapacityAnalyst     MeanReversionAgent (future)
            PortfolioRebalancer MomentumAgent      (future)
                                OptionsIncomeAgent (future)
                                StrategyAdvisor
                                PortfolioCoach
                                OptimizerAgent
                                BacktestOrchestrator
              │
        MEMORY STORE
  ─────────────────────────────────────────────────────
  Thread memory   → current conversation context
  Session memory  → today's trading day (SQLite checkpoint)
  Long-term memory→ strategy performance history, preferences
  Team memory     → shared: MarketScan writes → WaveSignal reads
```

---

### Layer 1 — Research (runs 6:00–9:15 AM pre-market, LLM-powered)

**MarketScan**
Scans F&O universe for unusual OI buildup, IV anomalies, and wave signal confluence. Produces the daily pre-market briefing. Writes findings to team memory so WaveSignal and StrategyAdvisor can read them during the day without re-scanning.

**NewsAnalyst**
Reads overnight corporate announcements, earnings releases, and macro data for symbols in the current portfolio. Generates plain-language summaries relevant to open positions. Example: "RELIANCE earnings tonight — recommend reducing position by 30% before close."

**RegulatoryWatcher** (pure Python scraper, no LLM)
Scrapes NSE and SEBI circulars daily. Detects changes that affect: lot sizes, STT rates, margin requirements, expiry calendar. Auto-updates `config/fee_schedules.json` if rates changed. Flags anything requiring human review.

---

### Layer 2 — Analysis (runs nightly or on-demand, mostly pure Python)

**RegimeDetector** (pure Python — HMM + VIX analysis)
Classifies current market state using a Hidden Markov Model on Nifty OHLCV, India VIX level and direction, rolling Sharpe of each active strategy, and options PCR. Outputs:
```python
RegimeScore {
    regime: "CHOPPY_BULL",          # TRENDING_BULL | TRENDING_BEAR | CHOPPY_BULL | HIGH_VOL_EVENT
    confidence: 0.78,
    strategy_weights: {
        "spider_wave":      0.15,   # low — SMA crossover struggles in choppy markets
        "mean_reversion":   0.55,   # high — range-bound favours mean reversion
        "options_income":   0.30,   # medium — low VIX = good for premium selling
    }
}
```
Capital allocation changes **gradually** (Carver's principle — no cliff-edge switching). A strategy producing near-zero forecast gets near-zero capital. The transition from one regime to another takes 5–10 trading days.

**FeatureEngineer** (pure Python — runs nightly)
Manages the ML signal feature pipeline used by strategy agents. Converts time bars → dollar bars (Jansen: stationary features). Applies fractional differentiation to prices (preserves memory while achieving stationarity). Calculates feature importance using MDI/MDA methods. Flags and removes spurious features. Feeds clean features to SpiderWaveAgent and future ML-driven strategies.

**ValidationPipeline** (pure Python — orchestrates LEAN, on-demand)
Automates Davey's full 5-gate sequence in a single call. You trigger once, it runs all gates sequentially and returns a single PASS/FAIL report:
```
ValidationPipeline("SpiderWave", universe="fno", period="2019-2024")
  Gate 1 → In-Sample backtest 2019-2021        → Sharpe 0.82   PASS
  Gate 2 → Walk Forward Optimization            → WFO Sharpe 0.51 PASS
  Gate 3 → Monte Carlo (10,000 shuffles)        → 96% positive  PASS
  Gate 4 → CPCV                                 → Mean 0.44     PASS
  Gate 5 → Out-of-Sample 2022-2024              → Sharpe 0.39   PASS
  ─────────────────────────────────────────────────────────────
  OVERALL: PASS — strategy approved for live trading
```
You still review and decide. The agent makes the **running** automatic, not the **decision**.

**PortfolioRebalancer** (pure Python — runs weekly or on drift trigger)
Manages long-term equity holdings (stocks bought for months/years — completely separate from algo trading). Implements three algorithms:

*Algorithm 1 — Carver Buffered Target Position:*
Target weight per stock = HRP weight × (current forecast / max_forecast). Buffer zone = ±3% around target. Only rebalances when drift exceeds buffer — prevents paying transaction costs on micro-movements. This reduces rebalancing trades by ~70% vs naive daily rebalancing.

*Algorithm 2 — CPPI (Constant Proportion Portfolio Insurance):*
$\text{Risky Allocation} = M \times (\text{Portfolio Value} - \text{Floor})$
where M = multiplier (e.g., 3×), Floor = minimum value to protect. Market rises → cushion grows → more equity. Market falls → cushion shrinks → less equity. Automatically reduces risk exposure in drawdowns.

*Algorithm 3 — Volatility Targeting (Carver):*
$\text{Equity Exposure} = \frac{\text{Target Annual Vol}}{\text{Realised 30\text{-}day Vol}} \times \text{Capital}$
India VIX low → increase equity. India VIX high → reduce equity. RegimeDetector output tightens the floor during HIGH_VOL_EVENT regimes.

*India Tax Gate (mandatory):*
- Never sell a position within 90 days of its 1-year LTCG threshold
- Harvest losses before March 31 to offset gains
- Time large LTCG realisations across financial years to use ₹1.25 lakh exemption

Output is always a **proposal table** — never auto-executes:
```
Symbol     Action  Current%  Target%  Drift   Tax Note
HDFC       HOLD    8.2%      7.8%     +0.4%   Within buffer — do nothing
RELIANCE   BUY     5.1%      7.0%     -1.9%   Buy ₹47,450 worth
INFY       SELL    12.3%     9.0%     +3.3%   ⚠ LTCG eligible in 45 days — DEFER
TCS        SELL    11.8%     9.0%     +2.8%   LTCG eligible — safe to sell
```

**CapacityAnalyst** (pure Python)
Estimates maximum capital that can trade the current strategy before slippage begins to erode returns. Key formula: capacity ≈ (daily volume × acceptable market impact %) × trading days. Example: "Spider Wave can trade up to ₹8 crore before slippage exceeds 15 bps per trade."

---

### Layer 3 — Decision (runs during and after market hours, mixed)

**StrategyRouter** (pure Python — runs every 60 seconds during market hours)
Takes RegimeDetector's latest weights and smoothly adjusts capital allocation across active strategies using Carver's gradual reweighting. Updates the `strategy_registry` SQLite table. Never makes LLM calls — pure weight arithmetic.

**StrategyRegistry** (SQLite table, not an agent)
Records: `strategy_id | name | regime_affinity | rolling_20d_sharpe | is_active | current_capital_weight`. New strategies register here. StrategyRouter reads this table. No code changes needed in Supervisor or PortfolioCoach when a new strategy is added.

**SpiderWaveAgent** (LEAN strategy — runs inside LEAN engine)
Multi-timeframe wave-following strategy. See Spider Wave documentation in strategies/spider-wave/. Standard interface: `run(universe, regime_context) → SignalList`. All strategy agents share this interface.

**[Future] MeanReversionAgent, MomentumAgent, OptionsIncomeAgent**
Each is a LEAN strategy + thin Python wrapper exposing the standard interface. Registered in StrategyRegistry. StrategyRouter assigns them capital based on regime. No other system changes needed.

**StrategyAdvisor** (LLM-powered — on-demand)
Explains StrategyRouter decisions in plain language. Example: "Why is the system running mostly mean reversion?" → reads RegimeDetector output and StrategyRegistry → explains in plain English why each strategy has its current weight and what would need to change to shift allocation.

**PortfolioCoach** (LLM-powered — on-demand)
Reviews overall portfolio health across both algo positions and long-term holdings: correlation between positions, concentration risk, days to expiry for options. Suggests rebalancing actions (PortfolioRebalancer executes them). The distinction: Coach *explains and recommends*, Rebalancer *calculates and proposes*.

**OptimizerAgent** (pure Python — on-demand, offline)
Accepts a strategy name and parameter space. Runs LEAN Grid Search (small spaces) or Euler Search (continuous). Runs Monte Carlo on the best result. Returns a ranked parameter heatmap. Feeds best parameters back to StrategyRegistry.

**BacktestOrchestrator** (LLM entry + pure Python execution)
Accepts natural language backtest requests. Translates to structured LEAN config. Launches `QuantConnect.Lean.Launcher.exe`. Waits for completion. Reads result JSON. Returns formatted statistics + equity curve. Primary interface: Claude Desktop via MCP.

---

### Layer 4 — Execution (on user action)

**OrderAssist** (LLM-powered)
Accepts natural language order descriptions. Translates to verified order parameters. Calls pre-margin check via broker API. Presents confirmation summary. Only sends to broker after explicit human approval. Never auto-executes.

**JournalAgent** (pure Python — after every trade)
Records each significant decision with full context to SQLite:
```json
{
  "date": "2026-03-16",
  "signal": "SpiderWave NIFTY — bullish alignment, forecast +14",
  "regime": "TRENDING_BULL, confidence 0.82",
  "strategy_weight": "0.65 (high — right regime)",
  "agent_recommendation": "Buy 24200 CE debit spread",
  "margin_confirmed": true,
  "decision": "EXECUTED",
  "outcome": "+₹8,400 (82% of max profit)",
  "lessons": ""
}
```
Queryable: "show all trades where I overrode the agent" or "what's the win rate when MarketScan flagged unusual OI buildup first?"

---

### Layer 5 — Monitor (always-on background, zero LLM, event-driven)

**RiskGuard** (pure Python — event-driven, every tick)
Hard real-time risk enforcement. Listens to Redis tick stream. On every position update computes live P&L and drawdown. At 3% portfolio drawdown: sends alert. At 5%: liquidates all positions immediately. Latency target: < 200ms from tick to action. **Never blocked by LLM calls. Never polls on a timer.** This is the only agent with authority to auto-execute without human confirmation (emergency stop only).

**RiskAnalyst** (LLM-powered — on-demand only)
Deep portfolio risk analysis requested by you. Computes: VaR, CVaR, Greeks exposure, correlation matrix, regime-adjusted stress test, days-to-expiry concentration. Completely separate from RiskGuard — never runs during market hours unless you specifically ask.

---

### Agent Time Schedule (from Durenard's priority queue principle)

```
06:00–09:15  Pre-market (research batch)
    RegulatoryWatcher  — scrapes SEBI/NSE circulars
    RegimeDetector     — recalculates regime from yesterday's close
    MarketScan         — scans OI, IV, wave signals (1 LLM call for summary)
    NewsAnalyst        — reads overnight announcements for held positions

09:15–15:30  Market hours (MINIMAL agent activity)
    RiskGuard          — event-driven every tick, ~0.1ms, pure Python
    StrategyRouter     — recalculates weights every 60 seconds, pure Python
    Supervisor         — only when you send a message
    OrderAssist        — only when you type an order
    ⚠ ALL OTHER AGENTS SLEEPING — no analytical LLM calls during market hours

15:30–18:00  Post-market (daily batch)
    FeatureEngineer    — rebuilds ML features with today's data
    JournalAgent       — records today's trades
    PortfolioRebalancer— checks drift against Carver buffer, generates proposal if needed

Nightly / Weekend (heavy batch — only when triggered)
    ValidationPipeline — multi-hour 5-gate test suite
    OptimizerAgent     — parameter search across strategy space
    BacktestOrchestrator — full historical backtest
```

---

### Memory System

All 19 agents share a single SQLite checkpoint store (`agents/memory.db`):

| Scope | Contents | Lifetime |
|---|---|---|
| Thread memory | Current conversation context | Until conversation ends |
| Session memory | Today's regime, MarketScan findings, open signals | Until market close |
| Long-term memory | Backtest history, parameter versions, trade journal | Permanent |
| Team memory | MarketScan → WaveSignal pipeline data | 24 hours rolling |

Key property: agents are **lazy** — they exist in memory only when called, then garbage-collected. Between calls, only the SQLite state persists. Peak memory per agent call: ~100MB for 50–200ms, then freed. This is why 19 agents do not slow the system down.

---

### MCP Integration (Claude Desktop)

The MCP server exposes **one tool: `trading_system`**. Claude calls it with natural language. The Supervisor routes internally. You never need to know which agent is handling the request.

```
Claude: "run Spider Wave backtest on BankNifty for last 3 years and optimize it"
  → MCP → Supervisor → BacktestOrchestrator → LEAN → OptimizerAgent → formatted result
  
Claude: "what's the current regime and which strategies are active?"
  → MCP → Supervisor → RegimeDetector (reads cached result) → StrategyAdvisor → explanation

Claude: "rebalance my long-term portfolio"
  → MCP → Supervisor → PortfolioRebalancer → proposal table (awaits your confirmation)
```

---

## PHASE MAINTENANCE — Operational Hardening  
**Timeline: After Phase 2 (weeks 17+)**  
**Goal: Production-grade operational tasks, automation, and monitoring**

These are non-critical for Phase 0→1→2 validation but essential for production deployment. They should be scheduled into sprints after the main feature phases are complete.

### Maintenance Task M1 — Liquidity Classifier + Universe Auto-Discovery

**Purpose**: Automatically detect new liquid stocks as they list and filter illiquid symbols before download.

**Why it matters**: In production, the app should not download all 2,460 NSE stocks (most are illiquid). Instead, it should:
1. Weekly monitor NSE FO contracts for new underlyings (auto-discover newly listed stocks with derivatives)
2. Validate each new stock meets liquidity thresholds (Bhavcopy volume > 100k/day, intraday bars > 10/hour, price > ₹50)
3. Remove delistings and suspended companies automatically
4. Maintain `approved_universe.csv` that `intraday_downloader.py` reads

**Implementation**:
```python
# New module: data-pipeline/liquidity_classifier.py
def discover_new_liquid_stocks():
    """Weekly job: scan NSE FO contracts for new underlyings"""
    fresh_contracts = download_nse_instrument_master()
    new_underlyings = extract_new_contracts(fresh_contracts, old_contracts)
    
    for stock in new_underlyings:
        avg_vol = get_bhavcopy_volume(stock, days=5)
        intraday_bars_per_hour = sample_dhan_intraday(stock, hours=1)
        price_level = get_bhavcopy_close(stock)
        
        if avg_vol > 100000 and intraday_bars_per_hour >= 10 and price_level > 50:
            approved_universe.add(stock)
            schedule_download(stock, start_date=2024-01-01)

def remove_dead_stocks():
    """Weekly job: remove delistings and illiquid stocks"""
    delistings = query_nse_corporate_actions(type="DELISTING")
    
    for stock in current_universe:
        try:
            dhan_data = fetch_dhan_1min(stock, date.today(), 1)
            if len(dhan_data) == 0:
                universe.remove(stock)  # No data = delisted or suspended
        except DhanException as e:
            if "invalid security" in str(e):
                universe.remove(stock)
```

**Deliverables**:
- `liquidity_classifier.py` — 300 lines, metrics computation
- `approved_universe.csv` — updated weekly, consumed by `intraday_downloader.py`
- Workflow: NSE FO scan (weekly 6 AM) → validate volume + bars → update approved universe
- Tests: validate new-stock detection, removal of dead symbols, no false positives

**Effort**: 1 week (Phase Maintenance Sprint 1)

**Used by**: Phase 1+ backtests (feeds cleaner universe), Phase 3+ production deployment (only downloads liquid stocks)

---

### Maintenance Task M2 — Streamlit Dashboard v2 (Live Metrics)

**Current state** (Phase 0): Dashboard shows download progress, QuestDB row counts, backtest results.

**Needed for production**: Add live trading metrics during market hours: current positions, live P&L, today's trades executed, daily log of agent decisions, RiskGuard status.

**Dashboard sections**:
1. Download Progress (existing) — jobs completed/failed/pending
2. Data Status — last Bhavcopy date, last QuestDB ingest, min/max quote symbols
3. Backtest Results (existing) — last backtest equity curve
4. **[NEW] Live Positions** — stocks held, current price, P&L, Greek exposure (if options)
5. **[NEW] Current P&L** — total realized + unrealized, daily gain/loss chart
6. **[NEW] Today's Trades** — trade table with entry/exit prices, P&L per trade
7. **[NEW] Agent Log** — recent RegimeDetector regime change, StrategyRouter weight shifts, WaveSignal alerts
8. **[NEW] RiskGuard Status** — current portfolio drawdown %, max allowed %, next alert level

**Effort**: 1 week (Phase Maintenance Sprint 1)

**Used by**: Developer/trader monitoring during Phase 2 paper trading and Phase 3+ live trading

---

### Maintenance Task M3 — Monitoring Infrastructure (Prometheus + Grafana)

**Purpose**: Production-grade metrics collection and alerting.

**What to monitor**:
- Downloader: jobs/sec, failed job rate, API quota usage, last successful run time
- QuestDB: rows/sec ingestion, query latency p50/p95/p99
- WebSocket: connected clients, ticks/sec per symbol, connection drops/recoveries
- LEAN: backtest execution time, process memory, Python GC pauses
- Broker API: call latency, errors per endpoint, token refresh status
- Agents: LLM token usage, agent latency, memory per agent

**Deliverables**:
- `monitoring/prometheus-config.yml` — Prometheus scrape endpoints
- `monitoring/grafana-dashboards/` — 5 dashboards (data, engine, trading, agents, system)
- Alerting rules: page when downloader fails > 3 consecutive times, alert when WebSocket latency > 500ms

**Effort**: 2 weeks (Phase Maintenance Sprint 2)

**Used by**: Production operations (Phase 3+)

---

### Maintenance Task M4 — Backup + Disaster Recovery

**What to back up**:
- `instrument-master/` SQLite databases (symbol maps, lot sizes, fee schedules)
- `lean-data/` OHLCV archives (terabytes)
- Backtest results JSON
- Trading journal and trade records
- Agent configuration and strategy parameters

**Backup strategy**:
- Incremental daily backups to NAS/cloud (S3)
- Full backup weekly
- Point-in-time recovery for instrument-master (SQLite backup + WAL logs)
- Test restore quarterly

**Effort**: 1 week (Phase Maintenance Sprint 2)

**Used by**: Production operations (Phase 3+)

---


**Duration: Weeks 17–22**
**Goal: REST API complete, Supervisor + 5 core agents working, Claude Desktop integration**

This phase is the first time the backend is truly built as an API. Until now, everything was scripts. Now it becomes a server. The agent system is also wired up here — infrastructure first, then agents on top.

### Step 3.1 — FastAPI Application Structure

The FastAPI application has these endpoint groups:

The data endpoints serve historical OHLCV from QuestDB with symbol and date range parameters. They also serve the instrument master search so the frontend can find symbols by name.

The backtest endpoints accept strategy parameters and date range, launch a LEAN subprocess, return a job ID, and provide polling endpoints for status and results. Results include the full equity curve as JSON, trade list, and key metrics.

The live trading endpoints show current positions, pending orders, order history, and account balance from Dhan.

The agent endpoints accept natural language queries and return agent responses asynchronously via streaming (LangGraph supports streaming tokens).

The WebSocket endpoint broadcasts live ticks to connected frontend clients. This is the single WebSocket connection the frontend maintains for all live data.

### Step 3.2 — WebSocket Architecture

The WebSocket architecture is the most technically complex part of Phase 3. Understanding it is critical.

When the frontend opens a WebSocket connection to the FastAPI server, it subscribes to a set of symbols. The FastAPI WebSocket manager maintains a mapping from symbol to a set of connected clients. When a new tick arrives from Redis pub/sub, the manager pushes it to all clients subscribed to that symbol.

The key design constraint: the frontend must never connect directly to the broker WebSocket. All broker connections are server-side. The frontend connects only to the FastAPI WebSocket. This keeps broker credentials server-side and allows the server to be the single source of truth.

### Step 3.3 — Supervisor Agent + Memory Store

The Supervisor is the single entry point for all agent interactions. It reads every request (from frontend chat, MCP, or API), classifies the intent, and routes to the correct specialist agent. It never handles domain logic itself — only routing.

The SQLite memory store (`agents/memory.db`) is initialised here using LangGraph's `SqliteSaver` checkpointer. All agents in all subsequent phases write to and read from this store. Thread/session/long-term/team scopes are defined here.

### Step 3.4 — RiskGuard + StrategyRouter (always-on processes)

**RiskGuard** is started as a background asyncio task when the FastAPI server starts. It subscribes to the Redis tick stream. On every position update it computes live P&L and drawdown. At 3% portfolio drawdown it sends an alert via WebSocket to the frontend. At 5% it calls the emergency liquidation endpoint. Latency target < 200ms. It never makes LLM calls. It never polls a database.

**StrategyRouter** runs as a separate 60-second scheduler task. It reads RegimeDetector's latest cached output from the memory store, recalculates strategy capital weights, and updates the `strategy_registry` table. No LLM involvement.

### Step 3.5 — BacktestOrchestrator + OptimizerAgent

**BacktestOrchestrator**: LangGraph agent that accepts natural language backtest requests. Translates to a structured LEAN config, launches `QuantConnect.Lean.Launcher.exe`, waits for completion, reads result JSON, returns formatted statistics and equity curve data.

**OptimizerAgent**: Accepts a strategy name and parameter space. Runs LEAN Grid Search or Euler Search. Runs Monte Carlo on the best result. Returns ranked parameter heatmap. Stores best parameters in the `strategy_registry` SQLite table.

Both agents use LangGraph's `SqliteSaver` checkpointer — if a backtest or optimisation run is interrupted, it resumes from the last checkpoint rather than restarting from scratch.

### Step 3.6 — MCP Server

The MCP server is a FastMCP wrapper that exposes a single tool: `trading_system`. The Supervisor receives every call and routes internally. The MCP server config file is committed to the repo. Adding it to Claude Desktop is one JSON entry.

**Phase 3 Milestone: "Run Spider Wave backtest on NIFTY for 3 years and optimize it" works from Claude Desktop in under 10 minutes. RiskGuard is live and tested to trigger at 5% drawdown.**

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

### Step 4.4 — SpiderWaveAgent, StrategyRegistry, RegimeDetector, StrategyAdvisor

**SpiderWaveAgent** is the first registered strategy in `StrategyRegistry`. It implements the standard strategy interface: `run(universe, regime_context) → SignalList`. The regime context is a dict produced by RegimeDetector containing the current regime label, confidence, and suggested capital weights. SpiderWaveAgent uses the MTF wave hierarchy for signal generation and notes the regime context when it applies an IV filter (no debit spreads when VIX > 20 and regime is `HIGH_VOL_EVENT`).

**StrategyRegistry** is a SQLite table with columns: `strategy_id`, `name`, `regime_affinity` (JSON mapping regime→fit score 0–1), `rolling_sharpe` (30-day realised), `enabled`, `capital_weight`. StrategyRouter reads from this table every 60 seconds and updates `capital_weight` based on the product of `regime_affinity[current_regime]` × `rolling_sharpe`, normalised to sum to 1.0. This is Carver's gradual reweighting — no hard switches.

**RegimeDetector** is built here as a standalone component. It runs an HMM on Nifty50 OHLCV + VIX (loaded from QuestDB) and emits one of four regime labels: `TRENDING_BULL`, `TRENDING_BEAR`, `CHOPPY_BULL`, `HIGH_VOL_EVENT`. Output is cached to the team memory store with a 6-hour TTL. All agents that need regime context read from cache — they never retrigger the HMM.

**StrategyAdvisor** (LLM agent) explains StrategyRouter decisions in plain language: why did capital shift from SpiderWave to MeanReversion, which regime caused it, what conditions would reverse the shift.

**Phase 4 Milestone: StrategyRouter is live. Add a second stub strategy to StrategyRegistry and watch capital weights shift in real time as RegimeDetector changes regime. StrategyAdvisor explains every weight change in plain English.**

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

### Step 5.5 — Remaining Agents (complete the 19-agent system)

**PortfolioRebalancer** is the most algorithmically complex agent. It runs nightly or on demand. Given current holdings and the latest regime context, it produces a proposed rebalancing table (symbol, current weight, target weight, action, estimated tax impact). It applies four algorithms in sequence:

1. **Carver Buffer**: target weight ± 3% deadband. Only trade when drift exits the buffer. Saves ~70% of transaction costs versus constant rebalancing.
2. **CPPI Floor**: risky exposure = multiplier × (portfolio value − floor). Automatically reduces equity allocation as portfolio falls, restores as it recovers.
3. **Volatility Targeting**: equity allocation = (target volatility / realised 30-day volatility) × capital. When VIX spikes, equity shrinks automatically.
4. **India Tax Gate**: defer any sell where the holding crosses from STCG (<1 year, taxed at 20%) to LTCG (>1 year, taxed at 12.5%) within the next 90 days. Harvest offsetting losses before March 31.

PortfolioRebalancer produces a table — it never executes. OrderAssist executes after explicit human confirmation.

**PortfolioCoach** (LLM) explains portfolio health in plain language: correlation between positions, concentration risk, days until expiry for options, and interprets the PortfolioRebalancer proposal in terms a non-quant can act on.

**JournalAgent** records every trade decision: signal generated → regime at signal time → agent recommendation → human decision → execution outcome. QueryableL from Claude Desktop: "show me all trades where RegimeDetector was wrong."

**FeatureEngineer** produces ML-ready features for any strategy that needs them: converts time bars to dollar bars (removing time-based sampling bias), applies fractional differentiation (Jansen) to make price series stationary while preserving memory, and runs MDI/MDA feature importance to prune irrelevant inputs before model training.

**ValidationPipeline** automates Davey's 5-gate sequence in one call: In-Sample → Walk-Forward Optimisation → Monte Carlo → Combinatorial Purged Cross-Validation (CPCV) → Out-of-Sample. Returns a pass/fail verdict with the weakest gate highlighted.

**CapacityAnalyst** estimates maximum capital before slippage erodes returns, answers "how large can SpiderWave scale on NSE."

**RegulatoryWatcher** (pure Python, no LLM) scrapes SEBI/NSE circulars daily, auto-updates `config/fee_schedules.json` when charges change, flags circulars affecting open positions to the Supervisor.

**Phase 5 Milestone: Drop-down broker selector works. All 19 agents operational. PortfolioRebalancer produces a nightly rebalancing table with tax impact. Switch from Dhan to Zerodha in one click with zero code change.**

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

### Step 8.1 — Native Production Deployment Setup (No Docker)

Production deployment follows the same no-Docker architecture used in development: LEAN launcher, QuestDB, Redis, FastAPI backend, and Next.js frontend run as native services. Use Windows service wrappers (or systemd on Linux) with automatic restart policies, startup ordering, and health checks.

Reverse proxy and TLS are configured with Nginx/Caddy. Environment variables for secrets are managed via a `.env.example` template and per-host secure `.env` files. Documentation must include start/stop scripts, service recovery, backup/restore, and token refresh operations.

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
| Intraday download for mapped FnO underlyings | SQLite job queue, resumable, 75-day windows, parallel workers with shared 8 req/sec token bucket |

---

## 🔢 What to Build Right Now

Current execution order from where the project is now:

1. Finish Step 0.4 queue drain: run intraday downloader until pending is zero and failed is either zero or explicitly re-run/reconciled.

2. Run Step 0.5 writer end-to-end on latest downloaded minute data and verify expected LEAN zip output structure under `lean-data/equity/india/minute/`.

3. Run Step 0.9 quality checks and confirm `lean-data/quality_report.json` passes all critical checks (format, gaps, zero/negative anomalies).

4. Run Step 0.8 backtest again on refreshed minute data baseline and record reproducible metrics snapshot.

5. Lock Phase 0 milestone: native services startup sequence + downloader + writer + backtest + Streamlit dashboard all passing in one checklist run.

---

*Plan version: 4.0*  
*Books synthesised: 12 books + 3 research papers*  
*Key corrections: 15 identified and fixed*  
*Frontend phases: 11 sub-phases with detailed build order*  
*Data pipeline: complete with rate limiting, resumable queue, SEBI tracking*
