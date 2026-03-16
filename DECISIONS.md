# ⚡ Quick Decision Reference

> This file is the fast lookup. For full context and reasoning, see CONTEXT.md.

---

## Every Decision in One Table

| Topic | Decision | DO NOT use | Reason |
|-------|----------|-----------|--------|
| Trading engine | QuantConnect LEAN (Docker) | Backtrader, zipline, custom | Production-grade, India + global built-in, Python strategies |
| LEAN communication | Write config.json → subprocess → read result | Import LEAN as Python package | LEAN is C#. Python.NET bridge only works inside LEAN. |
| EOD data | NSE Bhavcopy (1 file/day = all stocks) | Per-symbol API loop | Loop fails at stock 40. Bhavcopy = 2000+ stocks in one download. |
| Intraday data | Dhan API + SQLite job queue | Simple loop | SQLite queue makes it resumable. Crash at job 400 → restart at 401. |
| Tick database | QuestDB | TimescaleDB, InfluxDB | 41× faster OHLCV queries. Built for financial data. Apache 2.0. |
| Pub/sub | Redis | Kafka, RabbitMQ | Sub-ms latency. Live tick fan-out to frontend clients. Broker credentials stay server-side. |
| Symbol maps | SQLite (instrument-master) | Hardcoded maps | Instruments change daily. SQLite is single-file, zero-config, fast reads. |
| Python indicators | TA-Lib | pandas-ta | C core, 2-4× faster, BSD license, 150+ indicators. pandas-ta maintainer warned of sustainability issues. |
| Frontend chart | KLineChart Pro (Apache 2.0) | TradingView Lightweight | LW Charts has NO drawing tools and NO indicators. KLineChart Pro has both, free. |
| TV Advanced Charts | Apply for free license (optional) | Buy TV license | Free for public web projects only. Apache 2.0 KLineChart is the guaranteed free path. |
| UI components | shadcn/ui + Tailwind | Material UI, Ant Design | Dark mode native, composable, MIT license. |
| Data grids | AG Grid Community | Custom grid | MIT, handles high-frequency row updates. Used by Bloomberg. |
| Backtest charts | Recharts | Custom D3 | MIT, React-native. Static data only — React state is fine here. |
| Options charts | D3.js | KLineChart, Recharts | IV surface heatmap and payoff diagrams need custom rendering only D3 can do. |
| Hot data state | Direct DOM mutation | React state | 200 ticks/sec in React state = 200 renders/sec = frozen UI. Direct DOM = instant. |
| Medium data state | Zustand + 5s polling | Redux | Positions/P&L update at human speed. Zustand is simpler, faster. |
| Agent framework | LangGraph | Custom loops, AutoGen | Stateful, human-in-the-loop, Ollama-compatible. Stateful is needed for multi-step tasks. |
| AI online | Claude API (claude-sonnet) | GPT-4, Gemini | Best reasoning for financial analysis. Already in use for this project. |
| AI offline | Qwen 2.5 via Ollama | No offline | RTX 3060 (12GB VRAM). Data stays local. No API costs. |
| Portfolio model | HRP (RiskParityPortfolioConstructionModel) | Markowitz, BlackLitterman | López de Prado (2020): HRP beats Markowitz OOS. No analyst views needed. |
| Execution model | VWAP (VolumeWeightedAveragePriceExecutionModel) | Market order | Johnson (DMA): VWAP minimises market impact in thin markets. |
| Fee model | Versioned by effective_from date | Hardcoded | SEBI changed STT Oct 2024. Hardcoded fees give wrong backtest P&L. |
| Lot sizes | lot_size_history table with date ranges | Fixed constant | SEBI changed Nifty 50→25 and BankNifty 15→30 in Dec 2024. |
| Validation | IS → WFO → Monte Carlo → CPCV → OOS | Backtest only | Davey + López de Prado combined. 5 gates must all pass. |
| First broker | Dhan | Zerodha (first attempt) | Dhan provides historical options OHLCV + OI. Zerodha does not freely. |

---

## Data Format Rules (NEVER Break These)

```
LEAN price format:    lean_price = int(raw_price * 10000)
                      ₹94.00 → 940000
                      
LEAN timestamp:       milliseconds since midnight
                      9:15 AM IST → 33,300,000 ms
                      
LEAN data path:       /Data/equity/india/minute/{symbol}/{YYYYMMDD}_trade.zip
                      /Data/equity/india/daily/{symbol}.zip

All storage:          UTC timestamps (LEAN converts to IST via market-hours-database.json)

Option expiry:        ALWAYS from broker instrument master. NEVER calculate from calendar.
                      NSE has non-standard expiry dates.
```

---

## SEBI Changes That Broke Things in 2024

These are facts, not opinions. These changes affect fee models, lot sizes, strategy universes, and margin calculations.

| Effective Date | Change | Impact on Our System |
|----------------|--------|---------------------|
| Oct 1, 2024 | STT: Futures 0.0125%→0.02%, Options 0.0625%→0.1% | fee_schedules.json versioned. Backtests before this use old rates. |
| Nov 20, 2024 | Weekly expiries: only Nifty50 (NSE) and Sensex (BSE) | BankNifty/FinNifty/MidcapSelect weekly options removed. Strategy universe changed. |
| Dec 24, 2024 | BankNifty lot size 15 → 30 | lot_size_history table. Margin calculations use date-aware lookup. |
| Dec 26, 2024 | Nifty lot size 50 → 25 | Same as above. |
| Feb 10, 2025 | No calendar spread margin benefit on expiry day | Spread strategies appear more profitable before this date in backtests. |
| Apr 1, 2025 | Intraday position limit monitoring begins | Live trading limit violation rules changed. |

---

## Dhan Rate Limits (Memorise These)

```
Historical data:    20 req/sec max (we use 8 for safety)
Option chain:       1 req per 3 seconds
Order placement:    25 orders/sec, 250/min, 500/hr, 5000/day
Market Quote:       1 request for up to 1000 instruments (batch this!)
Intraday window:    90 days per request (use 85 days to be safe)
Token lifetime:     24 hours (SEBI regulation)
Data API cost:      Free if 25 F&O trades/month, else Rs 499/month
```

---

## NSE Bhavcopy URLs

```bash
# Equity EOD
https://archives.nseindia.com/content/historical/EQUITIES/{YEAR}/{MON}/cm{DD}{MON}{YEAR}bhav.csv.zip
# Example: https://archives.nseindia.com/content/historical/EQUITIES/2024/DEC/cm31DEC2024bhav.csv.zip

# F&O EOD (OHLCV + OI for all futures and options)
https://archives.nseindia.com/content/historical/DERIVATIVES/{YEAR}/{MON}/fo{DD}{MON}{YEAR}bhav.csv.zip

# Instrument master (Dhan)
https://images.dhan.co/api-data/api-scrip-master.csv

# Instrument master (Zerodha) - no auth required
https://api.kite.trade/instruments

# NSCCL SPAN file (for margin calculation)
https://www.nseclearing.com/risk-management/equity-derivatives/
```

---

## AlgoLoop — What to Copy and What NOT to Copy

**Copy these patterns (translate to Python/React):**
- LEAN subprocess communication: write config.json → launch subprocess → read result.json
- Backtest UI structure: tabs for Config / Symbols / Parameters / Holdings / Orders / Trades / Charts
- Progress monitoring: parse LEAN stdout for progress messages
- Result reading: parse LEAN result JSON (statistics, equity curve, trades)

**Do NOT copy:**
- Any C# or WPF code (Windows-only, no browser)
- Chart libraries (StockSharp, OxyPlot — replace with KLineChart Pro + Recharts)
- Data providers (only US/crypto, no India)
- Broker integration (not implemented in AlgoLoop)

---

## The 4-Component Framework (Narang) — Quick Reference

Every strategy MUST have all four. Missing any one breaks the system.

```
1. ALPHA MODEL
   What:    Signal generation
   Ours:    Spider Wave MTF system → LEAN Insight(symbol, direction, confidence, duration)
   Rule:    Confidence maps to Carver's forecast scale (−20 to +20)

2. RISK MODEL  
   What:    When to stop trading
   Ours:    MaximumDrawdownPercentPortfolio(0.05) + MaximumDrawdownPercentPerSecurity(0.03)
   Rule:    These are LEAN built-ins. Do not write custom risk model until Phase 3+.

3. PORTFOLIO CONSTRUCTION
   What:    How much of each position
   Ours:    RiskParityPortfolioConstructionModel (HRP — Hierarchical Risk Parity)
   Rule:    Start with EqualWeighting in Phase 0 for simplicity. Upgrade to HRP in Phase 1.

4. EXECUTION MODEL
   What:    How to place orders
   Ours:    VolumeWeightedAveragePriceExecutionModel
   Rule:    VWAP is appropriate for NSE order sizes. Do not use market orders.
```

---

## Validation Gates — All 5 Must Pass Before Live

```
Gate 1: In-Sample Backtest
  Period:     2019–2021
  Method:     Euler optimization on parameters
  Pass:       Sharpe > 0.5, reasonable drawdown

Gate 2: Walk Forward Optimization
  Windows:    1-year IS, 6-month OOS, rolling
  Pass:       OOS Sharpe meaningfully positive in majority of windows

Gate 3: Monte Carlo Robustness (Davey)
  Method:     Shuffle 10,000 times, compute Sharpe each shuffle
  Pass:       95%+ of shuffles show positive Sharpe

Gate 4: CPCV — Combinatorial Purged Cross-Validation (López de Prado)
  Method:     Purge adjacent bars, combinatorial test sets
  Pass:       Distribution of results centered above zero with low variance

Gate 5: Out-of-Sample
  Period:     2022–2024 (never touched during optimization)
  Pass:       Sharpe within 30% of Gate 2 WFO Sharpe

If any gate fails → strategy goes back to alpha redesign.
If all pass → proceed to Phase 2 paper trading.
```

---

## Frontend Data Architecture — The Critical Rules

```
HOT DATA (ticks, 100–200/sec):
  DO:    WebSocket singleton → callbacks → element.textContent = newPrice
  NEVER: WebSocket → setState() → React render
  
MEDIUM DATA (positions, P&L, orders — every 5 seconds):
  DO:    Zustand store + REST polling every 5 seconds
  OK:    React re-renders at 5-second intervals are fine
  
COLD DATA (settings, config, strategy params):
  DO:    Normal React state, React Query
  Fine:  Re-renders on user action are fine
```

---

*For questions not answered here, read CONTEXT.md. For the full development plan, read PLAN.md.*
