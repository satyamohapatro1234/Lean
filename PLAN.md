# 🌍 Global AI Trading Platform — Master Development Plan (v3.0)

**Repo:** https://github.com/satyamohapatro1234/Lean  
**Engine:** QuantConnect LEAN (C# core, Python strategy support)  
**Goal:** Production-grade, open-source, AI-native global trading terminal  
**First broker:** Dhan (provides historical options + OI data)  
**Status:** Phase 0 — Foundation  
**Plan version:** 3.0 — Built from 12 books + deep research

---

## 📚 Complete Book Reference Library

### Foundation Books (Read First — The Architecture Bible)

| # | Book | Author | Year | What It Teaches Us |
|---|------|--------|------|-------------------|
| 1 | **Inside the Black Box** (3rd ed) | Rishi K. Narang | 2024 | The 4-component system framework (Alpha/Risk/Portfolio/Execution) — the spine of our architecture |
| 2 | **Algorithmic Trading & DMA** | Barry Johnson | 2010 | Market microstructure, transaction costs, execution algorithms — the 200-page reason our cost model exists |
| 3 | **Building Winning Algorithmic Trading Systems** | Kevin J. Davey | 2014 | The complete validation sequence: IS → WFO → Monte Carlo → OOS — without this we will overfit |
| 4 | **Machine Learning for Algorithmic Trading** (2nd ed) | Stefan Jansen | 2020 | Data pipeline, feature engineering, corporate actions, ML strategy development |
| 5 | **Advances in Financial Machine Learning** | Marcos López de Prado | 2018 | Why standard backtests lie, HRP portfolios, meta-labeling, CPCV for proper validation |

### Modern Books (2019–2025) — What the Previous Plan Missed

| # | Book | Author | Year | Key Addition to Our Plan |
|---|------|--------|------|--------------------------|
| 6 | **Systematic Trading** | Robert Carver | 2015 | Forecast diversification, position sizing framework — the "how much" engine |
| 7 | **Leveraged Trading** | Robert Carver | 2019 | Safe leverage use, cost-adjusted returns, trading costs kill most strategies |
| 8 | **Advanced Futures Trading Strategies** | Robert Carver | 2023 | 30 tested strategies across futures — global market expansion reference |
| 9 | **Machine Learning for Asset Managers** | Marcos López de Prado | 2020 | HRP (Hierarchical Risk Parity) replaces Markowitz — our portfolio optimizer upgrade |
| 10 | **Causal Factor Investing** | Marcos López de Prado | 2023 | Causal ML vs correlation — how to find real alpha vs spurious signals |
| 11 | **Trading and Exchanges** | Larry Harris | 2002 | Market microstructure, order types, exchange mechanics — still the reference text |
| 12 | **Professional Automated Trading** | Eugene Durenard | 2013 | Full infrastructure design: OMS, data pipeline, event-driven architecture |

### Research Papers (2023–2025) — Frontier Knowledge

| Paper | Finding Relevant to Our Platform |
|-------|----------------------------------|
| "Reinforcement Learning for Quantitative Trading" (ACM 2023) | PPO and SAC outperform rule-based strategies; RL agent is Phase 3 extension for our AI agents |
| "From Deep Learning to LLMs: AI in Quantitative Investment" (arXiv 2025) | LLM agents (QuantAgent, Alpha-GPT 2.0) already doing strategy discovery — validates our agent architecture |
| "Advancing Algorithmic Trading with LLMs" (OpenReview 2025) | Human-in-the-loop LLM agents with inter-agent debate — confirms LangGraph is right choice |

---

## ⚠️ All Mistakes Identified and Corrected

### Mistake 1 — Missing Narang's 4-Component Framework (v2.0 fixed this, v3.0 strengthens it)
The previous plan added the framework but didn't specify HOW each component connects to LEAN's built-in models. Now specified:
- **Alpha:** Spider Wave Python algorithm → emits `Insight(symbol, direction, magnitude, confidence)`
- **Risk:** `MaximumDrawdownPercentPortfolio(0.05)` + `MaximumDrawdownPercentPerSecurity(0.03)` 
- **Portfolio Construction:** Start with `EqualWeighting`, migrate to `RiskParityPortfolioConstructionModel` (López de Prado's HRP via LEAN built-in)
- **Execution:** `VolumeWeightedAveragePriceExecutionModel` (uses VWAP, minimizes market impact per Johnson)

### Mistake 2 — Data Pipeline Was Misplaced (v2.0 fixed this)
Moved to Phase 0. Confirmed correct.

### Mistake 3 — Transaction Costs Missing (v2.0 fixed this)
Confirmed DhanFeeModel + VolumeShareSlippageModel in Phase 0. Additionally: Carver's "Leveraged Trading" shows that even 0.1% round-trip cost destroys most short-term strategies. We must measure actual slippage per trade in paper trading before going live.

### Mistake 4 — Validation Sequence Incomplete (v2.0 added Monte Carlo)
v3.0 adds **CPCV (Combinatorial Purged Cross-Validation)** from López de Prado (2018). WFO + Monte Carlo + CPCV together give 3 independent confirmations of strategy robustness. CPCV is more rigorous than WFO alone for finance because it handles the non-IID nature of financial time series.

### Mistake 5 — Portfolio Construction Was Wrong (NEW in v3.0)
v2.0 chose `EqualWeightingPortfolioConstructionModel` as starter. Correct per Narang. But it should migrate to **HRP (Hierarchical Risk Parity)** not Black-Litterman. Reason: López de Prado (2020) shows HRP out-of-sample outperforms Markowitz Mean-Variance and is more stable. LEAN has `RiskParityPortfolioConstructionModel` built in. Black-Litterman requires subjective views — we have no macro views to input.

### Mistake 6 — Corporate Actions Missing (v2.0 added this)
Confirmed. Added FactorFile generation to data pipeline. v3.0 adds: NSE delisting history must be maintained (survivorship bias from Jansen). LEAN MapFiles track this.

### Mistake 7 — Options Data Assumed Free (v2.0 solved via Dhan)
Confirmed. Dhan provides historical options OHLCV + OI data. This is the key reason Dhan is first.

### Mistake 8 — Frontend Too Late (v2.0 added Streamlit in Phase 0)
Confirmed and kept. v3.0 upgrades to: Streamlit for Phase 0 monitoring, full React terminal in Phase 7.

### Mistake 9 — Wrong Database Choice (NEW in v3.0)
v2.0 chose TimescaleDB. **Research shows QuestDB is correct for our use case.**
- QuestDB ingests 1.4M rows/second on modest hardware (vs 145K for TimescaleDB)
- QuestDB is specifically designed for financial tick data (founded by ex-low-latency trading engineers)
- QuestDB query performance: 25ms for OHLCV aggregation vs 1,021ms TimescaleDB
- TimescaleDB is better for PostgreSQL teams wanting familiar tooling — we're not that
- **Decision: QuestDB replaces TimescaleDB**

### Mistake 10 — No Carver Position Sizing Framework (NEW in v3.0)
Carver's "Systematic Trading" introduces the **forecast diversification multiplier** and **instrument diversification multiplier**. These are critical when running Spider Wave across multiple instruments (NIFTY, BANKNIFTY, stocks). Without them, a system trading 20 instruments with correlated signals will massively concentrate risk. This must be implemented in the Portfolio Construction Model.

### Mistake 11 — Charting Strategy Was Vague (NEW in v3.0)
v2.0 said "TradingView Charting Library (free for non-commercial)". **This is wrong.** Research reveals:

#### TradingView Charting Library — Full Truth

| Product | License | Drawing Tools | Indicators | Use Case |
|---------|---------|---------------|------------|----------|
| **TradingView Widgets** | Free, copy-paste | ❌ | ❌ | Simple embeds, no data feed |
| **TradingView Lightweight Charts** | Apache 2.0, fully open source | ❌ (limited) | ❌ (none built-in) | Price line charts only |
| **TradingView Advanced Charts** | Free for PUBLIC web projects, requires application + attribution | ✅ 80+ tools | ✅ 100+ indicators | Full professional chart |
| **TradingView Trading Platform** | Commercial license required | ✅ | ✅ | + Order ticket, DOM |

**Key finding:** TradingView does not provide Advanced Charts for personal use, hobbies, studies, or testing. Licenses are provided only to companies/individuals for use in public web projects. Must apply at tradingview.com/advanced-charts.

The free license is intended for public access services only — NOT for private, personal or internal uses.

**Our project is open-source and public** → we CAN apply for the free Advanced Charts license. But we cannot guarantee approval. We need a fallback.

**Decision: Dual charting strategy**
1. **Primary:** KLineChart + KLineChart Pro (Apache 2.0, fully open source, zero dependencies, professional drawing tools) — our guaranteed free solution
2. **Optional upgrade:** Apply for TradingView Advanced Charts free license — if approved, swap as optional build flag

#### Why KLineChart is the Right Choice

- Apache 2.0 license, zero dependencies, runs on mobile, TypeScript support
- Built-in indicators: MA, EMA, BOLL, MACD, RSI, KDJ, BIAS, CCI, DMI, OBV, SAR, and more
- Full drawing tools: trend lines, channels, Fibonacci, Gann fans, horizontal rays
- KLineChart Pro is the out-of-the-box financial chart built on KLineChart — Apache 2.0 license
- Actively maintained (3,591 stars, TypeScript, 10,000+ weekly downloads)
- Datafeed API pattern matches TradingView's (easy future migration)

### Mistake 12 — Technical Indicator Strategy Unclear (NEW in v3.0)
The plan had no decision on which indicator library to use for Python backend calculations (needed for backtesting, strategy development, agent analysis).

**Decision:**
- **Python backend:** TA-Lib (C core, BSD license, fastest, 150+ indicators, 60+ candlestick patterns, 2-4x faster than pandas-ta). Open-source BSD license, can be freely integrated in open-source or commercial applications. Use via `ta-lib-python` package.
- **Frontend:** KLineChart built-in indicators (no additional library needed)
- **Research/notebook:** `pandas-ta-classic` (150 indicators + 62 TA-Lib candlestick patterns, community maintained fork)

### Mistake 13 — Wrong Tick Data Storage Architecture (NEW in v3.0)
Previous plan had: Redis (live ticks) → TimescaleDB (historical storage). This creates unnecessary complexity with 2 systems.

**New architecture based on research:**
- **QuestDB** handles BOTH real-time ingestion AND historical queries in one system
- QuestDB has native WebSocket ingestion API
- QuestDB PostgreSQL wire protocol → existing SQL tools work
- Redis retained only for pub/sub (broadcasting ticks to multiple frontend WebSocket subscribers)

```
Broker WebSocket → Redis pub/sub → Frontend WebSocket clients
                ↓
              QuestDB (append-only tick table, partitioned by day)
                ↓
           LEAN /Data folder (LEAN zip format, generated from QuestDB queries)
```

---

## 🏗️ Final System Architecture (v3.0)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     GLOBAL AI TRADING PLATFORM v3.0                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              REACT FRONTEND (Next.js + TypeScript)               │    │
│  │                                                                  │    │
│  │  KLineChart Pro (Apache 2.0) ← Main trading chart               │    │
│  │  • 80+ drawing tools (Fibonacci, Gann, Channels, Rays)         │    │
│  │  • Built-in indicators (MA, MACD, RSI, BOLL, KDJ, OBV etc)    │    │
│  │  • Custom indicator API (plug in any Python TA-Lib output)      │    │
│  │  • Real-time WebSocket data feed                                │    │
│  │                                                                  │    │
│  │  Watchlist   OptionChain  StrategyBuilder  AIAssistant          │    │
│  │  Positions   OrderBook    BacktestResults  SpiderWave           │    │
│  │  Portfolio   HRPWeights   EquityCurve      MCValidation         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                           │ WebSocket + REST API                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  FASTAPI BACKEND (Python)                        │    │
│  │                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │              AGENTIC LAYER (LangGraph)                    │  │    │
│  │  │  Phase 3: BacktestOrchestrator | RiskMonitor | Optimizer │  │    │
│  │  │  Phase 4: WaveSignal | StrategyAdvisor                   │  │    │
│  │  │  Phase 5: NewsAnalyst | OrderAssist | MarketScan         │  │    │
│  │  │  MCP Server → Claude Desktop compatible                  │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  │                              │                                   │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │         LEAN ENGINE WRAPPER (AlgoLoop pattern)            │  │    │
│  │  │  write config.json → subprocess LEAN → read result.json  │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  │                              │                                   │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │     NARANG'S 4-COMPONENT FRAMEWORK (via LEAN)             │  │    │
│  │  │  Alpha:     Spider Wave → Insight(symbol, Up/Down, conf)  │  │    │
│  │  │  Risk:      MaxDrawdownPortfolio(5%) + PerSecurity(3%)    │  │    │
│  │  │  Portfolio: EqualWeight → HRP (López de Prado)            │  │    │
│  │  │  Execution: VWAPExecutionModel (Johnson's recommendation) │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  │                              │                                   │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │          UNIVERSAL SYMBOL MAPPER (SQLite)                 │  │    │
│  │  │          Dhan → Zerodha → Upstox → Angel → IB            │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ LEAN ENGINE   │  │   QUESTDB     │  │   REDIS    │  │ AI MODELS  │  │
│  │ (Docker)      │  │ (tick storage)│  │ (pub/sub)  │  │ Claude API │  │
│  │ Backtesting   │  │ 1.4M rows/sec │  │ live feed  │  │ Qwen Ollama│  │
│  │ Live Trading  │  │ SQL queries   │  │ to frontend│  │ RTX 3060   │  │
│  │ HRP Optimizer │  │ /Data export  │  │            │  │            │  │
│  └───────────────┘  └───────────────┘  └────────────┘  └────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Charting & Technical Analysis Stack (Complete Decision)

### Frontend Charts — KLineChart (Primary, 100% Free)

```
KLineChart (Apache 2.0, zero dependencies)
├── KLineChart Pro (Apache 2.0) — out-of-the-box professional chart
├── Built-in indicators: MA, EMA, SMA, BOLL, SAR, BIAS, CCI, MACD, DMI,
│                        RSI, KDJ, ROC, MTM, VR, OBV, SAR, TRIX, EMV, DMA
├── Drawing tools: trend lines, rays, channels, Fibonacci retracements,
│                  Fibonacci fan, Fibonacci circle, Fibonacci spiral,
│                  Fibonacci time zone, Gann fans, Gann squares,
│                  parallel channels, price notes, time markers
├── Chart types: candlestick, hollow candle, OHLC bars, area, step line
├── Multi-pane: main chart + sub-charts (volume, indicators)
├── Custom indicator API: register any indicator computed in Python
└── Real-time: update via WebSocket push
```

**How custom indicators from TA-Lib reach the chart:**
```
LEAN/TA-Lib (Python) → compute indicator → push via WebSocket → KLineChart
```

### Optional: TradingView Advanced Charts (Apply for Free License)
Apply at https://www.tradingview.com/advanced-charts/
- If approved: 100+ indicators, 80+ drawing tools, Pine Script indicators
- Requirement: must be a public web project, TradingView attribution required
- Risk: approval not guaranteed, TradingView can revoke license
- Strategy: build everything on KLineChart first, swap charts as optional config

### Python Technical Indicators — TA-Lib

```
TA-Lib (C core, BSD license — freely usable in open-source or commercial)
├── 150+ indicators: all standard (RSI, MACD, Bollinger, ATR, Stoch, ADX...)
├── 60+ candlestick patterns: Doji, Hammer, Engulfing, Morning Star...
├── Performance: 2-4x faster than pandas-ta (C implementation)
├── Integration: LEAN's built-in indicators + TA-Lib for extra indicators
└── Install: pip install ta-lib (binary wheels now available, no C compile needed)
```

### Backtest Visualization — Recharts + D3.js
- Equity curve: Recharts (React, MIT)
- Options payoff graphs: D3.js (BSD)
- OI heatmap: D3.js

---

## 🗄️ Data Storage Final Decision — QuestDB

**QuestDB replaces TimescaleDB. Reasons:**

1. **Performance:** QuestDB is compelling for quant research thanks to outstanding query performance and a gentler learning curve. It achieves 25ms for OHLCV aggregation vs 1,021ms for TimescaleDB.

2. **Designed for trading:** QuestDB was built by ex-low-latency trading engineers. Its storage model is time-based arrays — exactly like financial tick data.

3. **Ingestion speed:** QuestDB achieves 959K rows/sec with 4 threads, compared to TimescaleDB's 145K rows/sec. On AMD Ryzen5, QuestDB hits 1.43 million rows per second.

4. **Single system:** QuestDB handles both real-time ingestion AND historical queries. TimescaleDB needs more PostgreSQL expertise.

**Complete storage architecture:**
```
Storage Layer:
├── QuestDB          → all tick data, OHLCV bars, OI snapshots
│   ├── ticks table: (timestamp, symbol, price, volume, bid, ask)
│   ├── ohlcv table: (timestamp, symbol, timeframe, O, H, L, C, V)
│   └── option_chain: (timestamp, symbol, strike, expiry, ce_price, pe_price, ce_oi, pe_oi)
├── Redis            → pub/sub only (broadcast live ticks to WebSocket clients)
├── SQLite           → instrument master, symbol maps, user config, strategy params
└── /Data folder     → LEAN zip format files (read by LEAN engine)
```

---

## 📊 Carver Position Sizing Framework (NEW Addition)

From "Systematic Trading" and "Advanced Futures Trading Strategies" (Carver):

Every signal has a **forecast** (scaled between -20 and +20). The target position is:
```
target_position = (capital × target_risk × forecast_scalar × instrument_weight) 
                  / (price × point_value × instrument_vol × sqrt(252))
```

This prevents the portfolio from over-concentrating when many correlated signals fire.  
Spider Wave emits signals — these signals must be converted to forecasts before Portfolio Construction.

**What this means for our code:**
```python
# In Spider Wave algorithm (strategies/spider-wave/alpha_model.py)
def EmitInsights(self, data):
    wave_signal = self.calculate_wave_signal()
    
    # Convert to LEAN Insight (Carver's forecast → confidence mapping)
    if wave_signal == "GRANDMOTHER_UP":
        confidence = 0.9   # strongest signal
    elif wave_signal == "MOTHER_UP":
        confidence = 0.6   # medium signal
    elif wave_signal == "SON_UP":
        confidence = 0.3   # weakest signal
    
    return [Insight(symbol, InsightType.Price, timedelta(days=5),
                    InsightDirection.Up, confidence=confidence)]
```

---

## ✅ Plan Verification: Is v3.0 Correct?

Running through all book requirements:

**Narang check:** 4-component framework → ✅ Alpha/Risk/Portfolio/Execution all defined with specific LEAN models  
**Johnson check:** Transaction costs from day 1 → ✅ DhanFeeModel + VWAPExecution + VolumeShareSlippage  
**Davey check:** Full validation sequence → ✅ IS → WFO → Monte Carlo → CPCV → OOS  
**Jansen check:** Data quality + corporate actions → ✅ FactorFiles + delisting history + QuestDB quality checks  
**Carver check:** Position sizing + forecast diversification → ✅ Added to Spider Wave alpha model  
**López de Prado check:** HRP portfolio + CPCV validation → ✅ RiskParityPortfolioConstructionModel + CPCV added  
**Charting check:** 100% free/open source with drawing tools → ✅ KLineChart Pro (Apache 2.0)  
**Database check:** Performance for tick data → ✅ QuestDB replaces TimescaleDB  

**One remaining open question:** LEAN's Python API vs subprocess. Current plan uses subprocess (AlgoLoop pattern). This is correct for isolation — backtests run in separate process, cannot crash the FastAPI server.

---

## 📋 Development Phases (v3.0 — Final Corrected Order)

---

### Phase 0 — Foundation (Weeks 1–4)
**Goal:** First working backtest with all 4 components, correct data, realistic costs

**Infrastructure:**
- [ ] LEAN Docker container (QuantConnect official image)
- [ ] QuestDB Docker container
- [ ] Redis Docker container
- [ ] Docker Compose combining all three
- [ ] `engine_wrapper.py` (AlgoLoop pattern: config → subprocess → result.json)

**Instrument Master (Dhan first):**
- [ ] `instrument-master/schema.sql` — SQLite unified DB schema
- [ ] `instrument-master/brokers/dhan_parser.py` — parse Dhan CSV
- [ ] `instrument-master/daily_refresher.py` — 6 AM daily download job

**Symbol Mapper:**
- [ ] `symbol-mapper/universal_mapper.py` — implements LEAN `ISymbolMapper`
- [ ] Dhan security_id ↔ LEAN Symbol conversion
- [ ] Unit tests: round-trip equity + option + future

**Data Pipeline:**
- [ ] Dhan historical data downloader (equities, options, futures)
- [ ] LEAN data format writer (millisecond timestamps + 10000x prices)
- [ ] Corporate actions downloader (NSE splits/dividends)
- [ ] FactorFile generator (price adjustment for backtesting)
- [ ] Data quality checker (outlier removal, gap detection)
- [ ] QuestDB ingestion pipeline

**4-Component Framework (Spider Wave v1):**
- [ ] `strategies/spider-wave/alpha_model.py` — wave signals → Insight objects with Carver confidence mapping
- [ ] Risk: `MaximumDrawdownPercentPortfolio(0.05)` + `MaximumDrawdownPercentPerSecurity(0.03)`
- [ ] Portfolio: `EqualWeightingPortfolioConstructionModel` (start simple, upgrade to HRP in Phase 1)
- [ ] Execution: `VolumeWeightedAveragePriceExecutionModel` (Johnson's market impact minimizer)
- [ ] Fees: `DhanFeeModel` (exact fee structure)
- [ ] Slippage: `VolumeShareSlippageModel(0.001)` (0.1% conservative)

**Monitoring:**
- [ ] Streamlit dashboard: live QuestDB tick display, backtest P&L chart, positions

**Milestone:** `python run_backtest.py` produces a full JSON result with Sharpe, drawdown, trade log, and realistic transaction costs

---

### Phase 1 — Strategy Validation (Weeks 5–10)
**Goal:** Prove Spider Wave has real edge using Davey's + López de Prado's full validation stack

**Validation Sequence:**
- [ ] In-sample backtest: Spider Wave 2019–2021 on NSE NIFTY 50 universe
- [ ] Walk Forward Optimization (LEAN built-in Euler/Grid search)
- [ ] **Monte Carlo robustness test** (Davey): shuffle 10,000 times, confirm Sharpe > 0.5 in 95%+ of runs
- [ ] **CPCV** (López de Prado): combinatorial purged cross-validation — finance-specific, non-IID aware
- [ ] Out-of-sample: 2022–2024 (true test of real edge)
- [ ] Capacity analysis: max AUM before slippage kills edge
- [ ] Upgrade portfolio to **HRP** (`RiskParityPortfolioConstructionModel`) — test if Sharpe improves

**Carver Position Sizing:**
- [ ] Implement forecast scaling (−20 to +20 range) in Spider Wave
- [ ] Implement instrument diversification multiplier (across NIFTY + BANKNIFTY + stocks)
- [ ] Verify position sizes are safe for realistic capital (₹10L minimum)

**Milestone:** Spider Wave passes all 4 validation gates OR is sent back to alpha redesign

---

### Phase 2 — Dhan Live Integration (Weeks 11–16)
**Goal:** Dhan WebSocket live data + paper trading for 2 weeks minimum

- [ ] Dhan WebSocket client → QuestDB tick storage
- [ ] Redis pub/sub → Frontend WebSocket real-time display
- [ ] Dhan order API (market, limit, SL, SL-M, bracket orders)
- [ ] Positions/holdings/orders sync
- [ ] Daily 6 AM token refresh automation
- [ ] Symbol mapper verified on LIVE data (not just historical)
- [ ] 2-week paper trading run with full logging
- [ ] Slippage measurement: compare expected vs actual fill prices
- [ ] Adjust `VolumeShareSlippageModel` based on measured slippage

**Milestone:** Spider Wave runs 2 weeks paper trading on Dhan with zero crashes and measured transaction costs

---

### Phase 3 — Core Agents + MCP Server (Weeks 17–22)
**Goal:** BacktestOrchestrator, RiskMonitor, OptimizerAgent working + Claude Desktop integration

**FastAPI Backend:**
- [ ] Full REST API (backtest/live/positions/orders/instruments/agents)
- [ ] WebSocket manager (live ticks → multiple frontend clients)
- [ ] LEAN subprocess manager (queue, status, results)

**LangGraph Core:**
- [ ] Base state machine with shared state
- [ ] Claude API (online) + Qwen/Ollama (offline, RTX 3060) both supported
- [ ] Human-in-the-loop approval before any live order fires

**3 Core Agents:**
- [ ] **BacktestOrchestrator**: "Backtest Spider Wave on NIFTY with Euler optimization 2020–2024" → full report
- [ ] **RiskMonitor**: polls positions every 60s, alerts on drawdown > 3%, auto-liquidate at 5%
- [ ] **OptimizerAgent**: "Find best EMA params for Spider Wave on BANKNIFTY" → ranked heatmap

**MCP Server:**
- [ ] `agents/mcp_server.py` using FastMCP
- [ ] Claude Desktop config file
- [ ] Test: full backtest cycle via Claude Desktop chat

**Milestone:** "Run 2-year Euler-optimized backtest on Spider Wave for NIFTY" in Claude Desktop → results in 5 minutes

---

### Phase 4 — Options Intelligence + 2 Agents (Weeks 23–30)
**Goal:** Full NSE options backtesting with Dhan historical data + StrategyAdvisor

**Options Data:**
- [ ] Live option chain fetcher (all strikes × expiries from Dhan WebSocket)
- [ ] Historical options data pipeline (Dhan historical → QuestDB → LEAN format)
- [ ] LEAN options backtesting verified (greeks, expiry assignment, margin)

**Options Analytics:**
- [ ] Black-Scholes Greeks calculator (Delta, Gamma, Theta, Vega, Rho)
- [ ] IV surface chart (strike × expiry × IV — D3.js heatmap)
- [ ] OI change heatmap (PCR, max pain, unusual OI)
- [ ] Payoff graph builder (D3.js — iron condor, straddle, spreads)

**2 Agents:**
- [ ] **WaveSignal Agent**: Spider MTF hierarchy → options structure recommendation
- [ ] **StrategyAdvisor Agent**: "bullish on NIFTY, low IV" → specific iron fly strikes

**Milestone:** Select and backtest a NIFTY iron condor using Dhan historical options data

---

### Phase 5 — More Brokers (Weeks 31–36)
**Goal:** Zerodha, Upstox, Angel One, Fyers all integrated

- [ ] Zerodha Kite Connect (instrument master + symbol mapper + live + backtest)
- [ ] Upstox API (free, no monthly fee — good for testing)
- [ ] Angel One SmartAPI
- [ ] Fyers API
- [ ] Broker selector UI: switch broker without code change
- [ ] Multi-broker comparison: same strategy, measure execution quality differences

**3 Remaining Agents:**
- [ ] **NewsAnalyst Agent**: NSE announcements + macro news → market sentiment
- [ ] **OrderAssist Agent**: "Buy 1 lot NIFTY 24000 CE, sell 24200 CE" → executes via chosen broker
- [ ] **MarketScan Agent**: scans all F&O for unusual OI/IV buildup

**Milestone:** Drop-down broker switch works; all 9 agents operational

---

### Phase 6 — Global Markets (Weeks 37–44)
**Goal:** Interactive Brokers integration for US, EU, Forex, Crypto

- [ ] IB TWS API (Python ibapi or ib_insync)
- [ ] IB instrument universe → SQLite (LEAN has IB symbol mapper built-in)
- [ ] US equities backtesting (S&P 500 data via LEAN datasets)
- [ ] Forex (EURUSD, USDINR) via IB or OANDA
- [ ] Crypto (Binance) via LEAN built-in Binance adapter
- [ ] European futures (Eurex) via IB
- [ ] Market hours database updated for all exchanges
- [ ] Currency conversion for multi-currency portfolio

**Milestone:** Spider Wave-equivalent strategy runs simultaneously on SPY (IB) and NIFTY (Dhan)

---

### Phase 7 — Full Frontend (Weeks 45–52)
**Goal:** Production-grade React trading terminal with professional charts

**Tech Stack:**
```
React 18 + TypeScript + Next.js App Router
Tailwind CSS + shadcn/ui (component primitives)
KLineChart Pro (Apache 2.0) — main trading chart
Recharts — equity curve, portfolio analytics
D3.js — options payoff, OI heatmap
Ag Grid Community (MIT) — positions, orders, order book
Zustand — global state management
TanStack Query — server state, data fetching
```

**AlgoLoop UI Pattern (translated to React):**
| AlgoLoop WPF | Our React Equivalent |
|-------------|---------------------|
| MarketsViewModel | DataProviders page |
| StrategiesViewModel | Strategies panel |
| BacktestView (tabs) | BacktestResults (Config/Symbols/Params/Holdings/Orders/Trades/Charts) |
| StockChartView (StockSharp) | KLineChart Pro |
| EquityChartView (OxyPlot) | Recharts equity curve |
| LogView | Log panel (WebSocket tail) |

**Screens:**
- [ ] Main terminal (chart + watchlist + AI assistant panel)
- [ ] Options chain page (live OI, IV surface, strategy builder)
- [ ] Research page (backtest runner, optimization results, MC validation)
- [ ] Portfolio page (positions, equity curve, HRP weights, Carver position sizes)
- [ ] Settings page (broker config, data providers, AI model selection)

**Milestone:** Full terminal at `localhost:3000`, all panels live with WebSocket data

---

### Phase 8 — Open Source Launch
- [ ] Docker Compose one-command setup: `docker compose up` → everything starts
- [ ] Documentation site (architecture, setup guide, strategy development)
- [ ] Demo video: backtest → optimize → validate → paper trade → live
- [ ] GitHub release v1.0
- [ ] Community Discord

---

## 🔑 All Technical Decisions (Final)

| Decision | Choice | Why |
|----------|--------|-----|
| Engine | QuantConnect LEAN | 10+ years production, India + global built-in |
| Primary chart | KLineChart Pro | Apache 2.0, professional drawing tools, free |
| Optional chart | TradingView Advanced Charts | Apply for free license (public project) |
| Python indicators | TA-Lib | C core, fastest, BSD license, 150+ indicators |
| Tick database | QuestDB | 1.4M rows/sec, designed for financial data |
| Cache/pub-sub | Redis | Sub-ms latency, WebSocket fan-out |
| Instrument DB | SQLite | Fast reads, zero config, sufficient for mapping |
| Agent framework | LangGraph | Stateful, human-in-the-loop, Ollama-compatible |
| AI (online) | Claude API | Best reasoning for trading analysis |
| AI (offline) | Qwen via Ollama | RTX 3060, no data leaves machine |
| Portfolio model | HRP (RiskParityPortfolioConstructionModel) | López de Prado: better than Markowitz OOS |
| Execution model | VWAP (VolumeWeightedAveragePriceExecutionModel) | Johnson: minimizes market impact |
| Position sizing | Carver forecast framework | Handles correlated signals correctly |
| Validation | IS + WFO + Monte Carlo + CPCV + OOS | Davey + López de Prado combined |
| First broker | Dhan | Historical options + OI data available |

---

## 🚧 Known Hard Problems (All Documented)

| Problem | Solution |
|---------|----------|
| NSE option expiry dates ≠ calendar | Always use broker's actual expiry from instrument master |
| LEAN 10000x price format | `lean_price = int(raw_price * 10000)` at writer level |
| Multi-timezone (NSE/NYSE/Crypto) | Always store UTC, LEAN converts via market-hours-database.json |
| Option chain subscription limits | Subscribe ATM ±10 strikes initially, expand on demand |
| Broker token expiry at midnight | Automated 6 AM refresh job |
| Survivorship bias | LEAN MapFiles track delistings, maintain full universe history |
| Non-IID financial time series | CPCV not WFO alone for validation (López de Prado) |
| Carver signal correlation | Forecast diversification multiplier across instruments |

---

## 🚀 What to Build Right Now

```
Week 1 — Start here, in this order:
1. docker-compose.yml with LEAN + QuestDB + Redis
2. instrument-master/schema.sql
3. instrument-master/brokers/dhan_parser.py
4. instrument-master/daily_refresher.py
5. symbol-mapper/universal_mapper.py
6. First test: resolve NIFTY24DEC24000CE → LEAN Symbol → back to Dhan ID

Week 2:
7. data-pipeline/lean_writer.py (10000x price format, correct zip structure)
8. strategies/spider-wave/main.py (minimal version, emits Insights)
9. lean-engine/engine_wrapper.py (AlgoLoop subprocess pattern)
10. First backtest: Spider Wave on NIFTY → any result → SUCCESS
```

---

*Last updated: March 2026*  
*Version: 3.0 — Built from 12 books + database benchmark research + charting license research*  
*Next update: After Phase 0 milestone is hit*
