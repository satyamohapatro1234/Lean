# 🌍 Global AI Trading Platform — Master Development Plan (v2.0)

**Repo:** https://github.com/satyamohapatro1234/Lean  
**Engine:** QuantConnect LEAN (open-source, battle-tested, C# core with Python algorithm support)  
**Goal:** World's first open-source, AI-native, multi-broker global trading terminal  
**First broker:** Dhan (provides historical options + OI data for download)  
**Status:** Phase 0 — Foundation

---

## 🔬 Research Findings

### 1. Agentic Framework + LEAN — YES, Already Proven

**Found:** [`taylorwilsdon/quantconnect-mcp`](https://github.com/taylorwilsdon/quantconnect-mcp) (85 stars, active)  
A production MCP server — Claude/GPT controls QuantConnect via natural language.  
Commands like: *"Run grid search on EMA, kill switch if loss > 5%, deploy to IB paper"*

**Our approach is superior:** Local LEAN engine + Indian brokers + offline AI. No cloud. No monthly fees.

**3 valid integration methods:**
```
METHOD 1 — MCP Server (Claude Desktop → our platform)
  Claude Desktop ──► Our MCP Server ──► Local LEAN Engine ──► Any Broker

METHOD 2 — LangGraph Agents via FastAPI (our main architecture)
  React UI ──► FastAPI ──► LangGraph Agents ──► LEAN CLI ──► Broker

METHOD 3 — Agent INSIDE LEAN Algorithm (most autonomous)
  LEAN Python Strategy ──► calls Ollama/Claude ──► gets signal ──► places order
```

### 2. AlgoLoop Analysis (Capnode/Algoloop)

**Cloned and read source code fully. Here is what it is:**

| Property | Value |
|----------|-------|
| Language | C# WPF (Windows desktop XAML app) |
| Last commit | July 2025 (still maintained!) |
| Charts | StockSharp.Xaml.Charting + OxyPlot |
| Platform | Windows ONLY (WPF = Windows Presentation Foundation) |
| LEAN link | Launches `QuantConnect.Lean.Launcher.exe` as a subprocess |
| Data providers | USA (from QuantConnect GitHub), GDAX crypto, Oanda forex |
| Missing | Indian brokers, live trading UI, real data download, broker config |

**How AlgoLoop connects to LEAN (critical pattern we reuse):**
```csharp
// AlgoLoop creates a config.json in a temp folder, then:
_process = new ConfigProcess("QuantConnect.Lean.Launcher.exe", ...);
_process.Start();
_process.WaitForExit(cancel, (folder) => PostProcess(folder, model));

// After LEAN finishes, reads result JSON:
string resultFile = Path.Combine(folder, $"{model.AlgorithmName}.json");
model.Result = File.ReadAllText(resultFile);
```

**AlgoLoop frontend — can we use it directly?**

**NO** — it is C# WPF, which is Windows-only desktop technology. Cannot run in a browser.  
Cannot be ported to React without full rewrite.

**What we TAKE from AlgoLoop:**
1. **The architecture pattern** — how it separates MarketsViewModel, StrategiesViewModel, BacktestViewModel
2. **The LEAN communication method** — write config.json → launch subprocess → read result.json
3. **The data model** — how BacktestModel, SymbolModel, ParameterModel are structured
4. **The backtest result parsing** — reads LEAN's output JSON, extracts statistics, trades, holdings, charts

**Our web equivalent:** React frontend → FastAPI → subprocess LEAN → read result JSON → WebSocket to frontend.  
Same pattern, different technology stack.

### 3. Dhan Historical Options Data

Dhan provides:
- Historical OHLCV data via API (equities + F&O)
- Historical OI (Open Interest) data
- Option chain snapshots
- EOD (End of Day) data download

This means we start with Dhan as our single broker. Once Dhan is fully working, adding others is just new parser + symbol mapper.

---

## ⚠️ Corrections to Previous Plan (Based on Books)

### Correction 1 — Narang's 4-Component Framework Was Missing
Every professional quant system needs:
```
Alpha Model → Risk Model → Portfolio Construction → Execution Model
```
The previous plan had Alpha (Spider Wave) and Execution (brokers). Risk Model and Portfolio Construction were absent. These are now defined in Phase 0.

**Chosen models:**
- Risk Model: `MaximumDrawdownPercentPortfolio` (5% hard stop, LEAN built-in)
- Portfolio Construction: `EqualWeightingPortfolioConstructionModel` initially, then Black-Litterman later (both LEAN built-in)

### Correction 2 — Data Pipeline Was Misplaced
Previous plan had data pipeline in Phase 2. You cannot prove the symbol mapper works without running a backtest. You cannot run a backtest without data. Fixed: data pipeline moves to Phase 0.

### Correction 3 — Transaction Costs Were Missing (Barry Johnson)
Johnson dedicates 200 pages to this. Backtests without realistic costs show false profit.
LEAN already has `ZerodhaFeeModel` with exact NSE charges (0.03%, max ₹20, STT, exchange fees, SEBI charges, stamp duty). Must be configured from day one, not added later.

### Correction 4 — Monte Carlo Robustness Test Missing (Davey)
Walk Forward tests out-of-sample performance. Monte Carlo tests if the edge is real or random by randomly shuffling trades. Both are required. Monte Carlo is NOT built into LEAN — must be written as Python post-processor.

### Correction 5 — Phase 3 (Agents) Was 4 Weeks for 9 Deliverables
That is 2-3 months of work. Split into 3 sub-phases. Core agents first, then options agents, then global agents.

### Correction 6 — Corporate Actions Were Absent (Jansen)
Unadjusted data causes false signals. Stock splits look like crashes. Dividends look like drops. LEAN handles this via FactorFiles and MapFiles — must be generated for Indian stocks.

### Correction 7 — Options Historical Data Is Not Free
NSE options historical data (with OI, IV, bid-ask) costs money. **Dhan solves this** for us since it provides historical options data as part of subscription. This is exactly why Dhan is the right first broker.

### Correction 8 — Frontend Was Too Late
Without a UI, phases 1-5 are invisible — all debugging via log files. A minimal Streamlit monitoring dashboard goes into Phase 0.

### Correction 9 — Timelines Were Too Aggressive
Doubled all timelines. A solid working backtest with correct transaction costs and clean data is 4 weeks of work, not 2.

---

## 🏗️ Full System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GLOBAL AI TRADING PLATFORM                       │
│              (AlgoLoop patterns + our tech stack)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              REACT FRONTEND (Next.js + TypeScript)            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │Watchlist │ │Option    │ │Strategy  │ │ AI Assistant │   │   │
│  │  │+ Charts  │ │Chain     │ │Builder   │ │ (Chat Panel) │   │   │
│  │  │(TV chart)│ │(live OI) │ │(payoff)  │ │ (LangGraph)  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │Positions │ │Backtest  │ │Portfolio │ │ Spider Wave  │   │   │
│  │  │Holdings  │ │Results   │ │Analytics │ │ Dashboard    │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘    │
│                         │ WebSocket + REST                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  FASTAPI BACKEND (Python)                    │   │
│  │                                                              │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │           AGENTIC LAYER (LangGraph)                  │    │   │
│  │  │  BacktestOrchestrator | RiskMonitor | MCP Server    │    │   │
│  │  │  WaveSignal | StrategyAdvisor | NewsAnalyst         │    │   │
│  │  │  OrderAssist | MarketScan | OptimizerAgent          │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │                              │                               │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │      LEAN ENGINE WRAPPER (AlgoLoop pattern)          │    │   │
│  │  │  1. Write config.json                               │    │   │
│  │  │  2. Launch QuantConnect.Lean.Launcher subprocess    │    │   │
│  │  │  3. Read result.json → parse → return to agent      │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │                              │                               │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │      NARANG'S 4-COMPONENT FRAMEWORK                 │    │   │
│  │  │  Alpha: Spider Wave (Python LEAN algorithm)         │    │   │
│  │  │  Risk:  MaximumDrawdownPercentPortfolio (5%)        │    │   │
│  │  │  Portfolio: EqualWeighting → BlackLitterman later   │    │   │
│  │  │  Execution: DhanFeeModel + VolumeShareSlippage      │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │                              │                               │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │      UNIVERSAL SYMBOL MAPPER (SQLite)                │    │   │
│  │  │  Dhan | Zerodha | Upstox | Fyers | Angel | IB      │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                      │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────────────┐ │
│  │ LEAN ENGINE   │  │  DATA STORAGE  │  │   AI MODELS            │ │
│  │ (Docker)      │  │  TimescaleDB   │  │   Claude API (online)  │ │
│  │               │  │  Redis (live)  │  │   Qwen/Ollama (offline)│ │
│  │  Backtesting  │  │  SQLite        │  │   RTX 3060 12GB VRAM   │ │
│  │  Live Trading │  │  /Data (LEAN)  │  │                        │ │
│  │  Optimization │  │                │  │                        │ │
│  └───────────────┘  └────────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 The 9 AI Agents (LangGraph)

| Agent | Role | Priority |
|-------|------|----------|
| **BacktestOrchestrator** | Natural language → designs + runs backtests | Phase 3 (core) |
| **RiskMonitor** | Watches live positions, fires alerts | Phase 3 (core) |
| **OptimizerAgent** | Grid/Euler search, interprets results | Phase 3 (core) |
| **WaveSignal** | Spider MTF Wave System signals | Phase 4 |
| **StrategyAdvisor** | Market view → optimal options structure | Phase 4 |
| **NewsAnalyst** | News sentiment → market impact | Phase 5 |
| **OrderAssist** | Natural language → order parameters | Phase 5 |
| **MarketScan** | Scans OI, IV, unusual activity globally | Phase 5 |
| **PortfolioCoach** | Daily P&L review, position sizing | Phase 5 |

---

## 📋 Development Phases (Corrected)

---

### Phase 0 — Foundation (Weeks 1–4)
**Goal:** One working backtest with realistic transaction costs, correct data, and Narang's 4-component framework

**Instrument Master:**
- [ ] Dhan instrument master downloader (CSV daily refresh)
- [ ] SQLite schema for unified instrument DB
- [ ] Dhan symbol parser → unified DB
- [ ] LEAN Symbol builder (from SQLite rows)

**Symbol Mapper:**
- [ ] `UniversalSymbolMapper` implementing LEAN's `ISymbolMapper`
- [ ] `dhan_to_lean(security_id)` → LEAN Symbol
- [ ] `lean_to_dhan(Symbol)` → Dhan security_id
- [ ] Unit tests for equity + options + futures

**Data Pipeline:**
- [ ] Dhan historical data downloader (equities)
- [ ] Dhan historical OI + options data downloader
- [ ] LEAN data format writer (milliseconds + 10000x prices, zip files)
- [ ] Corporate actions downloader (NSE - splits/dividends)
- [ ] FactorFile generator for Indian stocks (price adjustment)
- [ ] Data quality checks (outlier removal, gap filling)

**LEAN Setup:**
- [ ] Docker container with LEAN engine
- [ ] `engine_wrapper.py` — write config → launch subprocess → read results (AlgoLoop pattern)
- [ ] `backtest_runner.py` — full backtest pipeline
- [ ] `optimizer_runner.py` — Grid/Euler search

**4-Component Framework:**
- [ ] Alpha: Spider Wave Python algorithm (basic version)
- [ ] Risk: `MaximumDrawdownPercentPortfolio(0.05)` configured
- [ ] Portfolio: `EqualWeightingPortfolioConstructionModel` configured
- [ ] Execution: `DhanFeeModel` + `VolumeShareSlippageModel(0.001)` (0.1% slippage)

**Monitoring:**
- [ ] Streamlit dashboard (live tick feed, backtest P&L chart, positions)
- [ ] Log viewer

**Milestone:** `python run_backtest.py --strategy spider-wave --market NSE --years 3` → full PDF report with Sharpe, drawdown, transaction costs, win rate

---

### Phase 1 — Strategy Validation (Weeks 5–8)
**Goal:** Prove Spider Wave edge is real, not random (Davey's full validation sequence)

- [ ] In-sample backtest: Spider Wave 2019-2022 (NIFTY 50 universe)
- [ ] Verify transaction costs match Dhan's actual fee schedule
- [ ] Walk Forward Optimization: optimize parameters, test on unseen data
- [ ] Monte Carlo robustness test (Python post-processor on backtest results)
  - Randomly shuffle trade P&L 10,000 times
  - Check if Sharpe > 0.5 in 95%+ of simulations
  - If not — strategy has no real edge, back to alpha design
- [ ] Out-of-sample backtest: 2023-2024 (the true test)
- [ ] Capacity analysis: at what AUM does slippage kill the edge?

**Milestone:** Strategy passes all 4 validation gates (IS backtest → WFO → Monte Carlo → OOS)

---

### Phase 2 — Dhan Live Integration (Weeks 9–14)
**Goal:** Dhan WebSocket live ticks flowing into LEAN correctly

- [ ] Dhan WebSocket client (tick streaming)
- [ ] Tick → Redis pipeline (sub-second latency)
- [ ] Redis → LEAN live data feed adapter
- [ ] Dhan order placement (market, limit, SL, SL-M)
- [ ] Dhan positions/holdings/orders sync
- [ ] Paper trading test (1 week minimum)
- [ ] Verify symbol mapping is correct on live data
- [ ] Daily token refresh job (6 AM, TOTP automation)
- [ ] Error handling: reconnection, rate limits, token expiry

**Milestone:** `python live.py --broker dhan --mode paper` runs Spider Wave on NIFTY live for 1 week with no crashes

---

### Phase 3 — Core Agents + MCP (Weeks 15–20)
**Goal:** 3 core agents + MCP server working

**Infrastructure:**
- [ ] FastAPI with full LEAN REST wrapper
  - `POST /backtest/run` → launches LEAN → returns job_id
  - `GET /backtest/{id}/status` → running/complete/failed
  - `GET /backtest/{id}/results` → full JSON report
  - `POST /live/start` / `POST /live/stop`
  - `GET /positions` / `GET /orders` / `GET /holdings`
  - `GET /instruments/search?q=NIFTY`
- [ ] WebSocket endpoint for live tick streaming to frontend
- [ ] LangGraph state machine base (shared state, human-in-the-loop approval)
- [ ] Claude API integration (online) + Qwen/Ollama (offline, RTX 3060)

**3 Core Agents:**
- [ ] **BacktestOrchestrator Agent**
  - Input: natural language description
  - Output: runs backtest, returns full analysis
  - "Backtest Spider Wave on NIFTY with EulerSearch optimization 2020-2024"
- [ ] **RiskMonitor Agent**
  - Polls positions every 60 seconds
  - Fires alerts when drawdown approaches 5% limit
  - "Your NIFTY position is at 3.8% drawdown — approaching 5% kill switch"
- [ ] **OptimizerAgent**
  - "Find best EMA parameters for Spider Wave on BANKNIFTY"
  - Runs Grid or Euler search, returns ranked results with Sharpe heatmap

**MCP Server:**
- [ ] FastMCP server (same approach as quantconnect-mcp but local)
- [ ] Claude Desktop can control backtest, optimization, positions via chat
- [ ] Human approval required before any live order is placed

**Milestone:** Say "Run 2-year Euler-optimized backtest on Spider Wave for NIFTY" in Claude Desktop → full results + chart appear

---

### Phase 4 — Options Intelligence + 2 More Agents (Weeks 21–28)
**Goal:** Full NSE options suite with LEAN backtesting

**Options Data (Dhan):**
- [ ] Live option chain fetcher (all strikes, all expiries, bid-ask, OI, IV)
- [ ] Historical options OHLCV + OI downloader (Dhan historical data)
- [ ] LEAN options data writer (option zip format with Greeks)
- [ ] LEAN options backtesting working (iron condor, straddle, spreads)

**Options Analytics:**
- [ ] Greeks calculator (Delta, Gamma, Theta, Vega, Rho — Black-Scholes)
- [ ] IV surface chart (strike × expiry × IV heat map)
- [ ] OI change heatmap (PCR, max pain, unusual OI buildup)
- [ ] Strategy payoff graph (D3.js — visual P&L at expiry)
- [ ] Strategy Builder UI (add legs → see payoff → backtest → execute)

**2 More Agents:**
- [ ] **WaveSignal Agent** — integrates Spider MTF hierarchy into strategy selection
- [ ] **StrategyAdvisor Agent** — "market is bullish, low IV, suggest structure" → AI returns iron condor with exact strikes

**Milestone:** Select NIFTY iron condor in UI, AI calculates max profit/loss/breakevens, backtests it 1 year with Dhan historical options data

---

### Phase 5 — Add More Brokers (Weeks 29–34)
**Goal:** Zerodha + Upstox + Angel One + Fyers connected

- [ ] Zerodha Kite Connect integration (instrument master + symbol mapper + live)
- [ ] Upstox API integration (free, no monthly fee)
- [ ] Angel One SmartAPI integration
- [ ] Fyers API integration
- [ ] Broker selector in UI (choose which broker to trade with)
- [ ] Multi-broker paper trading (same strategy, compare execution quality)

**Milestone:** Switch broker dropdown from Dhan to Zerodha → same strategy runs without code change

---

### Phase 6 — Global Markets (Weeks 35–42)
**Goal:** Works with any exchange in the world

- [ ] Interactive Brokers integration (US, EU, Asia, Crypto, Forex)
- [ ] US equities backtesting (S&P 500, NASDAQ)
- [ ] Forex (EURUSD, USDINR) via IB or OANDA
- [ ] Crypto (Binance) via LEAN built-in adapter
- [ ] European markets (Eurex futures/options)
- [ ] Market hours database for all global exchanges
- [ ] Currency conversion for multi-currency portfolios
- [ ] Remaining 4 agents: NewsAnalyst, OrderAssist, MarketScan, PortfolioCoach

**Milestone:** Live strategy on SPY options (IB) and NIFTY options (Dhan) simultaneously

---

### Phase 7 — Full Frontend (Weeks 43–50)
**Goal:** Production-grade React trading terminal

Built using AlgoLoop's UI architecture patterns, but in React + TypeScript:

| AlgoLoop Component | Our React Equivalent |
|-------------------|---------------------|
| MarketsView (WPF) | DataProvider page (React) |
| StrategiesView (WPF) | Strategies panel (React) |
| BacktestView + tabs | BacktestResults with tabs |
| StockChartView (StockSharp) | TradingView Charting Library |
| EquityChartView (OxyPlot) | Recharts equity curve |
| LogView | Log panel with WebSocket |

**Deliverables:**
- [ ] React + TypeScript + Tailwind + shadcn/ui setup
- [ ] TradingView Charting Library (apply at tradingview.com/advanced-charts — free non-commercial)
- [ ] Watchlist with live prices (WebSocket)
- [ ] Option chain table (color-coded, sortable by strike/OI/IV)
- [ ] Strategy Builder with payoff graph (D3.js)
- [ ] Positions / Orders / Holdings panels
- [ ] Backtest results dashboard (replicating AlgoLoop's tabs: Config/Symbols/Parameters/Holdings/Orders/Trades/Charts)
- [ ] AI chat panel (BacktestOrchestrator + RiskMonitor responses)
- [ ] Spider Wave MTF dashboard
- [ ] Portfolio analytics (equity curve, drawdown, Sharpe over time)

**Milestone:** Full trading terminal at `localhost:3000` with all panels live

---

### Phase 8 — Open Source Launch
- [ ] Docker Compose one-click setup (`docker compose up` → everything starts)
- [ ] Documentation site (architecture, setup, strategy development guide)
- [ ] Demo video (Spider Wave backtest → optimize → paper trade → live)
- [ ] GitHub release v1.0
- [ ] Community Discord

---

## 🔑 Key Technical Decisions

### Why Dhan First?
1. Provides historical options OHLCV + OI data (most Indian brokers don't)
2. Modern REST + WebSocket API
3. Good documentation
4. Once Dhan works, adding others is a new parser + symbol mapper

### LEAN Data Format — The 10000x Rule
```python
# LEAN stores ALL prices as integers × 10,000
# ₹94.00 → stored as 940000 (integer)
# NSE 9:15 AM opening bar stored as:
# 33300000, 940000, 950000, 934000, 944000, 1047471
# ^ms since midnight           ^close     ^volume

# NEVER feed raw prices — LEAN will misinterpret everything
lean_price = int(raw_price * 10000)
ms_since_midnight = int((timestamp.hour * 3600 + timestamp.minute * 60 + timestamp.second) * 1000)
```

### LEAN Data Folder Structure
```
/Data/
├── equity/india/
│   ├── minute/{symbol}/{YYYYMMDD}_trade.zip   ← OHLCV minute bars
│   ├── daily/{symbol}.zip                      ← OHLCV daily bars
│   ├── factor_files/{symbol}.csv               ← Split/dividend adjustments
│   └── map_files/{symbol}.csv                  ← Ticker rename history
├── option/india/
│   └── minute/{symbol}/{YYYYMMDD}_trade.zip   ← Options OHLCV
├── index/india/
│   └── minute/{symbol}/{YYYYMMDD}_trade.zip   ← NIFTY 50, BANKNIFTY
└── market-hours/
    └── market-hours-database.json              ← NSE: 9:15-15:30 IST
```

### How LEAN Engine Communication Works (AlgoLoop Pattern)
```python
# From AlgoLoop's LeanLauncher.cs — we replicate this in Python
def run_backtest(strategy: str, config: dict) -> dict:
    # Step 1: Write config.json to temp folder
    tmpdir = tempfile.mkdtemp()
    with open(f"{tmpdir}/config.json", "w") as f:
        json.dump(config, f)
    
    # Step 2: Launch LEAN as subprocess
    process = subprocess.Popen(
        ["dotnet", "QuantConnect.Lean.Launcher.dll"],
        cwd=tmpdir, capture_output=True
    )
    process.wait()
    
    # Step 3: Read result JSON (same as AlgoLoop's PostProcess method)
    with open(f"{tmpdir}/{strategy}.json") as f:
        return json.load(f)  # Contains statistics, orders, trades, charts
```

### Transaction Cost Model (Barry Johnson)
```python
# LEAN configuration — must be set from day 1, not added later
# Dhan fee structure:
class DhanFeeModel(IndiaFeeModel):
    BrokerageMultiplier = 0.0003    # 0.03% or ₹20 max per order
    MaxBrokerage = 20               # ₹20 cap
    SecuritiesTransactionTax = 0.00025  # 0.025% on sell (equities)
    ExchangeTransactionCharge = 0.0000345
    StateTax = 0.18                 # 18% GST on brokerage
    SebiCharges = 0.000001          # ₹10 per crore
    StampCharges = 0.00003          # 0.003% on buy

# Slippage (conservative for NSE)
slippage = VolumeShareSlippageModel(0.001)  # 0.1% = ~1-2 ticks for liquid NSE stocks
```

### Data Storage Decision
```
Redis           → live ticks (sub-second, in-memory pub/sub)
TimescaleDB     → historical tick + candle storage (time-series SQL)
SQLite          → instrument master, symbol mappings, user config, strategy params
/Data folder    → LEAN zip format files (read by LEAN engine during backtest)
```

---

## 🚧 Known Hard Problems + Solutions

### Problem 1: NSE Option Expiry Date Mismatch
LEAN calculates expiry from calendar. NSE changes expiry dates for holidays.
**Solution:** Always use broker's actual expiry date from instrument master. Never calculate.

### Problem 2: LEAN 10000x Price Format
Raw prices from broker → LEAN misinterprets as prices 10000x smaller.
**Solution:** `lean_price = int(raw_price * 10000)` — enforce at data writer level.

### Problem 3: Multiple Time Zones
NSE: Asia/Kolkata (+5:30) | NYSE: America/New_York | LEAN uses UTC internally.
**Solution:** Always store ticks in UTC. LEAN converts via market-hours-database.json.

### Problem 4: Option Chain WebSocket Limits
Dhan WebSocket: limited simultaneous subscriptions.
Full NIFTY chain (all strikes × all expiries) = thousands of tokens.
**Solution:** Subscribe only to ATM ±10 strikes initially. Expand on demand.

### Problem 5: Broker Daily Token Expiry
All Indian brokers expire API tokens at midnight daily.
**Solution:** Automated 6 AM refresh using Playwright + TOTP. Or manual refresh UI.

### Problem 6: Corporate Actions (Stefan Jansen)
Stock splits, dividends, delistings cause false signals if data is unadjusted.
**Solution:** Download NSE corporate actions, generate LEAN FactorFiles, adjust prices.

### Problem 7: Survivorship Bias
Backtesting only on stocks that still exist overstates returns.
**Solution:** LEAN MapFiles track ticker renames/delistings. Maintain full universe history.

---

## 📁 Repository Structure

```
Lean/  (satyamohapatro1234/Lean)
├── PLAN.md                              ← This file (master plan)
├── README.md                            ← Project overview
├── requirements.txt                     ← Python dependencies
├── docker-compose.yml                   ← One-click setup
│
├── instrument-master/
│   ├── daily_refresher.py               ← Downloads all broker instrument files
│   ├── schema.sql                       ← SQLite unified instrument DB schema
│   └── brokers/
│       ├── dhan_parser.py               ← ✅ Build first
│       ├── zerodha_parser.py
│       ├── upstox_parser.py
│       ├── fyers_parser.py
│       ├── angelone_parser.py
│       └── ib_parser.py
│
├── symbol-mapper/
│   ├── universal_mapper.py              ← ISymbolMapper implementation
│   ├── lean_symbol_builder.py           ← Creates LEAN Symbol objects
│   └── tests/
│
├── data-pipeline/
│   ├── tick_collector.py                ← WebSocket → Redis
│   ├── candle_builder.py                ← Tick → OHLCV aggregation
│   ├── lean_writer.py                   ← OHLCV → LEAN zip format (10000x)
│   ├── historical_downloader.py         ← Pull historical data from Dhan
│   ├── factor_file_generator.py         ← Corporate actions → FactorFiles
│   └── data_quality_checker.py          ← Outlier removal, gap detection
│
├── brokers/
│   ├── base_broker.py                   ← Abstract broker interface
│   ├── dhan/                            ← ✅ Build first
│   │   ├── broker.py                    ← Dhan REST API implementation
│   │   ├── websocket_handler.py         ← Live tick streaming
│   │   ├── fee_model.py                 ← DhanFeeModel (LEAN IFeeModel)
│   │   └── config.example.json
│   ├── zerodha/
│   ├── upstox/
│   ├── fyers/
│   ├── angelone/
│   └── interactive-brokers/
│
├── lean-engine/
│   ├── engine_wrapper.py                ← AlgoLoop pattern: config → subprocess → result
│   ├── backtest_runner.py               ← Full backtest pipeline
│   ├── live_runner.py                   ← Live trading start/stop
│   ├── optimizer_runner.py              ← Grid + Euler search
│   ├── monte_carlo.py                   ← Davey's robustness test
│   └── config/
│       ├── backtest.json                ← LEAN backtest config template
│       ├── live.json                    ← LEAN live trading config template
│       └── optimizer.json               ← LEAN optimizer config template
│
├── strategies/
│   └── spider-wave/
│       ├── main.py                      ← Spider MTF Wave System (LEAN Python algo)
│       ├── alpha_model.py               ← Wave signal generation
│       ├── risk_model.py                ← MaximumDrawdownPercentPortfolio 5%
│       ├── portfolio_model.py           ← EqualWeighting → BlackLitterman
│       ├── config.json                  ← Parameters (optimizable via LEAN)
│       └── README.md
│
├── agents/
│   ├── orchestrator.py                  ← Main LangGraph state machine
│   ├── backtest_orchestrator_agent.py   ← Phase 3
│   ├── risk_monitor_agent.py            ← Phase 3
│   ├── optimizer_agent.py               ← Phase 3
│   ├── wave_signal_agent.py             ← Phase 4
│   ├── strategy_advisor_agent.py        ← Phase 4
│   ├── news_analyst_agent.py            ← Phase 5
│   ├── order_assist_agent.py            ← Phase 5
│   ├── market_scan_agent.py             ← Phase 5
│   ├── portfolio_coach_agent.py         ← Phase 5
│   └── mcp_server.py                    ← Claude Desktop compatible MCP
│
├── api/
│   ├── main.py                          ← FastAPI app
│   ├── routes/
│   │   ├── backtest.py
│   │   ├── live.py
│   │   ├── positions.py
│   │   ├── orders.py
│   │   ├── instruments.py
│   │   ├── agents.py
│   │   └── market_data.py
│   └── websocket_manager.py             ← Live data → frontend bridge
│
├── monitoring/
│   └── dashboard.py                     ← Streamlit (Phase 0 minimal UI)
│
├── frontend/                            ← Phase 7 full React terminal
│   ├── package.json
│   ├── next.config.js
│   └── src/
│       ├── components/
│       │   ├── Watchlist.tsx
│       │   ├── OptionChain.tsx
│       │   ├── StrategyBuilder.tsx
│       │   ├── TradingChart.tsx          ← TradingView Charting Library
│       │   ├── EquityCurve.tsx           ← Recharts (AlgoLoop OxyPlot equiv.)
│       │   ├── BacktestResults.tsx       ← Tabs: Config/Symbols/Params/Holdings/Orders/Trades/Charts
│       │   ├── AIAssistant.tsx
│       │   └── SpiderWaveDashboard.tsx
│       └── pages/
│           ├── index.tsx                 ← Main terminal
│           └── research.tsx              ← Research/backtest page
│
└── docs/
    ├── LEAN_DATA_FORMAT.md              ← Exact format spec (10000x, zip structure)
    ├── SYMBOL_MAPPING.md                ← How symbol mapping works
    ├── BROKER_SETUP.md                  ← Dhan setup guide
    ├── AGENT_ARCHITECTURE.md            ← LangGraph state machine design
    ├── ALGOLOOP_ANALYSIS.md             ← What we took from AlgoLoop
    └── API_REFERENCE.md                 ← FastAPI endpoint docs
```

---

## 🎯 Competitive Position

| Feature | Dhan | Sensibull | OpenAlgo | QuantConnect | **Our Platform** |
|---------|------|-----------|----------|--------------|--------------------|
| Open Source | ❌ | ❌ | ✅ | Partial | ✅ |
| Local LEAN Engine | ❌ | ❌ | ❌ | ❌ | ✅ |
| Multi-broker India | ✅ | ✅ | ✅ | ❌ | ✅ |
| Global Markets (IB) | ❌ | ❌ | ❌ | ✅ | ✅ |
| AI Agents (LangGraph) | ❌ | ❌ | ❌ | Partial | ✅ |
| Offline AI (Ollama RTX) | ❌ | ❌ | ❌ | ❌ | ✅ |
| MCP Server (Claude Desktop) | ❌ | ❌ | ❌ | Partial | ✅ |
| Options Backtesting | Limited | ❌ | ❌ | ✅ | ✅ |
| Strategy Validation (Davey) | ❌ | ❌ | ❌ | Partial | ✅ |
| Monte Carlo Robustness | ❌ | ❌ | ❌ | ❌ | ✅ |
| 4-Component Framework | ❌ | ❌ | ❌ | ✅ | ✅ |
| Spider Wave System | ❌ | ❌ | ❌ | ❌ | ✅ |
| AlgoLoop patterns (open) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Self-hosted | ❌ | ❌ | ✅ | ❌ | ✅ |

---

## 🚀 Right Now — First Code to Write

**Week 1 targets:**

1. `instrument-master/schema.sql` — SQLite schema for all broker IDs
2. `instrument-master/brokers/dhan_parser.py` — parse Dhan's master CSV
3. `instrument-master/daily_refresher.py` — download + store to SQLite
4. `symbol-mapper/universal_mapper.py` — Dhan ↔ LEAN Symbol translation
5. Run first test: resolve "NIFTY24DEC24000CE" → LEAN Symbol → back to Dhan security_id

That's it. One file flows into the next. No skipping.

---

*Last updated: March 2026*  
*Status: Phase 0 — Foundation*  
*Version: 2.0 (corrected based on Narang/Johnson/Davey/Jansen book analysis)*
