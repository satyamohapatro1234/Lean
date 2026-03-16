# 🖥️ Global AI Trading Platform — Complete Frontend Blueprint

**Version:** 1.0  
**Target:** Desktop only (min 1280px width)  
**Stack:** React 19 + TypeScript + Next.js 15 (App Router) + Tailwind CSS + shadcn/ui  
**AI Panel:** Floating chat bubble (bottom-right)  
**Markets:** Indian (NSE/BSE) + International (US Equities via Alpaca + Forex via OANDA)

---

## 📚 Research & Book References

Every decision below traces to a specific source.

| Decision | Source |
|----------|--------|
| 3-panel trading terminal layout | *Trading and Exchanges* — Larry Harris; Bloomberg Terminal reference |
| Direct DOM mutation for hot ticks | *High Performance Browser Networking* — Ilya Grigorik; WebSocket performance research |
| Zustand for medium state, TanStack Query for server state | *Designing Data-Intensive Applications* — Martin Kleppmann; Zustand vs Redux research 2025 |
| Never store server data in client state | "Federated State Done Right" (Nextsteps.dev, Dec 2025) |
| Backtest result panels (equity curve + drawdown + trade list + stats) | QuantConnect result page docs + TradingView Strategy Tester research |
| Scanner criteria builder pattern | Trade Ideas + Finviz UX analysis |
| Options chain OI color coding | Zerodha Kite + NSE website research |
| CSS flash animation for price change | Zerodha Kite UI pattern; professional terminal research |
| Floating AI chat bubble | Research: non-intrusive AI panels in professional tools (Devexperts case study) |
| Market context switcher | MT5 multi-asset research; SaxoTraderGO pattern |
| KLineChart Pro | Apache 2.0 license; drawing tools + indicators built-in; WebSocket integration support |
| AG Grid Community | High-frequency table update benchmarks; virtualisation for large lists |
| D3.js for options IV surface | Only library capable of custom financial surface rendering |
| Recharts for backtest equity curve | React-native, good static chart rendering; no WebSocket needed for backtest |
| Next.js App Router | React 19 compatibility; SSR for first load; server components for cold data |
| shadcn/ui + Tailwind | Professional dark theme out-of-box; no runtime CSS overhead |

---

## 🗺️ Complete Page Map

| Route | Page Name | Purpose | Markets |
|-------|-----------|---------|---------|
| `/` | **Dashboard** | Overview: market status, P&L summary, watchlist preview, recent alerts, AI briefing | All |
| `/terminal` | **Trading Terminal** | Main trading view: watchlist + chart + order entry | All |
| `/scanner` | **Scanner / Screener** | Criteria builder + results table + saved scans + alerts | All |
| `/backtest` | **Backtest Lab** | Strategy config + submit + results viewer | All |
| `/paper` | **Paper Trading Monitor** | Simulated live trading dashboard | All |
| `/options` | **Options Chain** | Full option chain + OI/IV analysis | India + US |
| `/portfolio` | **Portfolio Overview** | Holdings, P&L, allocations, performance | All |
| `/agents` | **AI Agent Hub** | Full-page agent session history + task management | All |
| `/settings` | **Settings & Brokers** | Broker connections, strategy config, user prefs | All |
| `/onboarding` | **Onboarding Wizard** | First-time broker setup flow | All |
| `/_auth/login` | **Login** | Auth page | — |

**The floating AI chat bubble is NOT a page** — it lives as a persistent component across all pages above.

---

## 🏗️ Application Shell — Global Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ GLOBAL NAVBAR (fixed, 48px tall)                                        │
│  [Logo] [Nav links] [Market Switcher] [Clock IST/ET] [Account] [Alerts]│
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                    PAGE CONTENT (fills remaining height)                │
│                                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                          [🤖 AI] ← Floating bubble BR
```

### Global Navbar Components
- **Logo** — app name + version
- **Nav links** — Dashboard | Terminal | Scanner | Backtest | Paper | Options | Portfolio | Agents
- **Market Switcher Dropdown** — `🇮🇳 India (NSE)` | `🇺🇸 US (Alpaca)` | `💱 Forex (OANDA)` — changes context across entire app
- **Live Clock** — shows IST when India active, ET when US active, UTC for Forex. Updates every second via `setInterval` (NOT WebSocket)
- **Market Status Badge** — `🟢 OPEN` / `🔴 CLOSED` / `🟡 PRE-MARKET`. Updates via REST poll every 60 seconds
- **Account Selector** — if multiple broker accounts connected
- **Notification Bell** — badge count; popover shows last 10 alerts
- **User Avatar** — dropdown: Profile, Settings, Logout

### Floating AI Chat Bubble
- Lives at `position: fixed; bottom: 24px; right: 24px; z-index: 9999`
- Collapsed state: circular button, 56px diameter, AI icon + green dot (online indicator)
- Expanded state: 400px wide × 600px tall chat panel slides up from bubble
- Chat panel sections: history messages at top, input box at bottom, "Agent: Supervisor" label
- Streaming: tokens arrive via SSE from `/api/v1/agents/chat/stream`
- Context-aware: knows what page user is on; what symbol is selected in terminal
- Close button: X in top-right of expanded panel

---

## 📄 Page 1: Dashboard (`/`)

### Purpose
The first thing a trader sees each morning. Shows what matters NOW without clicking anything.

### Layout
```
┌──────────────────────────────────────────────────────────────────────┐
│ MARKET STATUS BAR (full width, 40px)                                  │
│ India: 🟢 OPEN 14:23 IST | US: 🔴 CLOSED | Forex: 🟢 24H              │
├──────────────┬──────────────────────────────┬───────────────────────┤
│ LEFT COLUMN  │ CENTER COLUMN                │ RIGHT COLUMN          │
│ (280px)      │ (flex-grow)                  │ (320px)               │
│              │                              │                       │
│ Mini         │ INDEX TILES (row)            │ TODAY'S P&L           │
│ Watchlist    │ NIFTY 24,350 +1.2%           │ ▲ ₹ 12,450 (India)   │
│ (direct DOM) │ BANKNIFTY 52,100 +0.8%      │ ▲ $ 342 (US)          │
│              │ SENSEX 80,100 +0.9%         │ Portfolio Total       │
│ 10 symbols   │ INDIA VIX 12.4 ↓            │ ─────────────────     │
│ with LTP     │ SPY 580 +0.3% (if US mode)  │ RECENT ALERTS (5)    │
│ change       │                              │ OI buildup NIFTY      │
│ flash        │ MINI CHART (48h sparkline)   │ PDT warning triggered │
│              │ NIFTY 50 — 2-day area chart  │ Strategy signal       │
│              │ [Recharts AreaChart]          │ ─────────────────     │
│              │                              │ AI MORNING BRIEFING  │
│              │ OPEN POSITIONS SUMMARY       │ "MarketScan ran at    │
│              │ [AG Grid, 5 rows max]        │ 9:00 AM. Unusual OI  │
│              │ Symbol | Qty | LTP | P&L     │ buildup in NIFTY...  │
│              │                              │ [Read full →]"        │
│              │ AGENT ACTIVITY LOG           │                       │
│              │ [last 3 agent runs + status] │                       │
└──────────────┴──────────────────────────────┴───────────────────────┘
```

### Components and Their API Connections

**Market Status Bar**
- Component: `<MarketStatusBar />`
- Data: `GET /api/v1/market/status` — polled every 60 seconds via TanStack Query
- Response: `{ india: "OPEN" | "CLOSED" | "PRE", us: ..., forex: ..., india_close_in: "45 min" }`

**Mini Watchlist (Left Column)**
- Component: `<MiniWatchlist symbols={watchlistSymbols} />`
- Data: WebSocket subscription `{ type: "subscribe", symbols: [...] }`
- Update: **Direct DOM mutation** — `el.textContent = price.toFixed(2)` + CSS class flash
- Flash: add `flash-green` or `flash-red` class for 300ms on price change, then remove
- Click: navigates to `/terminal?symbol=NIFTY`

**Index Tiles**
- Component: `<IndexTile symbol="NIFTY" />`
- Data: WebSocket (same subscription as watchlist)
- Update: Direct DOM for LTP; Zustand for change% (updates every 5 seconds from snapshot)

**Mini Chart (48h sparkline)**
- Component: `<MiniSparkline symbol="NIFTY50" />`
- Data: `GET /api/v1/market/ohlcv/NIFTY50?resolution=15min&hours=48`
- Library: Recharts `<AreaChart>` — static REST data, no WebSocket needed here
- Does NOT update in real-time — refreshed every 15 minutes via TanStack Query

**Open Positions Summary**
- Component: `<PositionsSummary />`
- Data: Zustand `positionsStore` — populated via `GET /api/v1/portfolio/positions` every 5 sec
- AG Grid with 5 row limit, virtualised

**Agent Activity Log**
- Component: `<AgentActivityLog />`
- Data: `GET /api/v1/agents/status` — polled every 30 seconds
- Shows: agent name, last run time, status (running/complete/failed)

**Today's P&L**
- Component: `<DailyPnL />`
- Data: Zustand `portfolioStore` — `GET /api/v1/portfolio/pnl` every 5 seconds
- Market-separated: India ₹ / US $ / combined

**Recent Alerts**
- Component: `<AlertFeed />`
- Data: WebSocket event `{ type: "alert", ... }` + initial `GET /api/v1/scanner/alerts/recent`
- Shows last 5, click opens scanner page

**AI Morning Briefing**
- Component: `<AiBriefingCard />`
- Data: `GET /api/v1/agents/briefing` — REST, result of pre-market MarketScan agent run
- Static text, refreshes at 9:15 AM IST daily
- "Read full →" opens `/agents` page with that session

---

## 📄 Page 2: Trading Terminal (`/terminal`)

This is the most complex and most performance-critical page.

### Layout
```
┌───────────────────────────────────────────────────────────────────────┐
│ TERMINAL TOOLBAR (full width, 40px)                                    │
│ [Symbol Search] [Timeframe: 1m 5m 15m 1h 4h 1d 1w] [Indicator+]      │
│ [Drawing: cursor pencil line fib level rect text] [Layout: 1 2 4]    │
├──────────┬───────────────────────────────────────┬────────────────────┤
│ WATCHLIST│ CHART AREA                            │ ORDER PANEL        │
│ (240px)  │ (flex-grow, min 600px)               │ (280px)            │
│          │                                       │                    │
│ [+ Add]  │ KLineChart Pro                        │ MARKET SWITCHER   │
│          │ (Candlestick / Line / Heikin Ashi)   │ [India▼]           │
│ NIFTY    │                                       │                    │
│ 24350.50 │ Technical indicators overlaid         │ ORDER TYPE TABS   │
│ +1.2%    │ Volume bars at bottom                 │ [Buy] [Sell]       │
│          │                                       │                    │
│ BNKN     │ [Zoom: 1m 5m 15m 1h]                 │ Symbol: NIFTY      │
│ 52100    │                                       │ Type: [MIS▼]       │
│ +0.8%    │                                       │ Qty: [____]        │
│          │                                       │ Price: [MARKET▼]   │
│ RELIANCE │                                       │ Limit: [_____]     │
│ 1280.50  │                                       │ SL: [_____]        │
│ -0.3%    │                                       │ Target: [_____]    │
│          │ BOTTOM PANEL (collapsible, 200px)     │                    │
│ [India   │ ─────────────────────────────────     │ [Check Margin]     │
│  sector  │ TABS: Orders | Positions | Trade Tape │ Margin Req: ₹42,000│
│  indices]│ [AG Grid virtualised table]           │ Available: ₹180,000│
│          │                                       │ [Place Order]      │
│ [+ India │                                       │                    │
│ US toggle│                                       │ ORDER CONFIRMATION │
│ buttons] │                                       │ modal on submit    │
└──────────┴───────────────────────────────────────┴────────────────────┘
```

### Component Details

#### Watchlist Panel (240px left)
```
<WatchlistPanel>
  <SearchBar />                      ← search symbols, add to watchlist
  <WatchlistHeader />                ← title + sort options
  <WatchlistItem>                    ← one per symbol, direct DOM for price
    <span id="sym-NIFTY-name">
    <span id="sym-NIFTY-ltp">       ← DOM mutation target
    <span id="sym-NIFTY-chg">       ← DOM mutation target (% change)
    <span id="sym-NIFTY-bar">       ← CSS width % for mini bar
  </WatchlistItem>
  <SectorIndicesSection />           ← India: NIFTY sectors; US: SPY sectors
</WatchlistPanel>
```

**Data flow:**
1. Page load: `GET /api/v1/market/watchlist` → populate symbol list (React state, runs once)
2. WebSocket: `subscribe(symbols)` → callbacks update DOM directly per symbol
3. Add symbol: `POST /api/v1/market/watchlist` → re-fetch list
4. Remove: `DELETE /api/v1/market/watchlist/{symbol}` → remove from DOM

**Watchlist item click:** sets `activeSymbol` in Zustand `terminalStore` → chart reloads

#### Toolbar
```
<TerminalToolbar>
  <SymbolSearch />         ← command-K shortcut; fuzzy search against /api/v1/market/symbols
  <TimeframeSelector />    ← 1m 5m 15m 1h 4h 1d 1w buttons; sets terminalStore.timeframe
  <IndicatorPanel />       ← dropdown to add/remove: MACD, RSI, BB, EMA, VWAP, etc.
  <DrawingTools />         ← cursor, trend line, horizontal, fib, rectangle, text
  <LayoutSelector />       ← 1-chart, 2-chart side-by-side, 4-chart grid
  <ChartTypeSelector />    ← Candlestick | Line | Heikin Ashi | Renko
</TerminalToolbar>
```

#### Chart Area — KLineChart Pro
```
<ChartContainer>
  <KLineChartPro
    symbol={activeSymbol}
    timeframe={activeTimeframe}
    indicators={activeIndicators}
    drawings={savedDrawings}
    onBarUpdate={handleBarUpdate}
  />
</ChartContainer>
```

**How chart data loads:**
1. **Historical bars:** `GET /api/v1/market/ohlcv/{symbol}?resolution=5min&limit=500` via TanStack Query
2. Chart renders all bars
3. **WebSocket live:** on new tick, `wsManager.onTick(symbol, tick)` → chart's `updateLastBar(tick)` or `appendBar(newBar)` if new candle
4. **Timeframe change:** new REST fetch, chart re-renders with new data
5. **Drawings persistence:** saved to `localStorage` per symbol per timeframe (no server needed for v1)

**India vs US vs Forex chart differences:**
- India: volume in lots; OHLCV in ₹; market hours 9:15–15:30 IST; gaps on weekends + holidays
- US: volume in shares; OHLCV in $; pre/post market bars shown faded; EST timezone
- Forex: no volume bars (only tick volume); prices in pips; 24/5 no gaps Sunday-Friday

#### Order Panel (280px right)
```
<OrderPanel>
  <MarketContextBadge />           ← shows "India (Dhan)" or "US (Alpaca)" or "Forex (OANDA)"
  <BuySellTabs />                  ← tabbed Buy | Sell

  <OrderForm>
    <SymbolDisplay symbol={activeSymbol} />
    <ProductTypeSelector />        ← India: MIS | CNC | NRML; US: Day | GTC; Forex: Market
    <QuantityInput />              ← India: shows lot size info for F&O
    <OrderTypeSelector />          ← Market | Limit | Stop-Market | Stop-Limit | GTD
    <LimitPriceInput />            ← shown when Limit or Stop-Limit selected
    <StopLossInput />              ← optional; shown always
    <TargetInput />                ← optional; shown always
  </OrderForm>

  <MarginCheckButton />            ← calls POST /api/v1/orders/margin-check
  <MarginDisplay />                ← shows required vs available after check
  <PlaceOrderButton />             ← disabled until margin check passes
  <OrderConfirmationModal />       ← blocks submission; shows order summary; requires confirm
</OrderPanel>
```

**Order flow:**
1. User fills form → clicks "Check Margin"
2. `POST /api/v1/orders/margin-check` with `{symbol, qty, order_type, price, product_type}`
3. Response: `{required: 42000, available: 180000, allowed: true}`
4. "Place Order" button enables
5. User clicks "Place Order" → `OrderConfirmationModal` opens
6. Modal shows: symbol, qty, type, price, margin, total value
7. User confirms → `POST /api/v1/orders` → success toast OR error with broker message

**India-specific order panel rules:**
- If F&O instrument: show lot size, lot count input alongside quantity
- MIS products: show "Auto SQ-Off at 3:20 PM" warning badge
- Post 3:00 PM: show warning "Market closes in X minutes; MIS positions will be squared off"

**US-specific:**
- PDT warning if < 4 day trades in 5 days AND account < $25K
- Extended hours toggle (Alpaca supports 4 AM – 8 PM ET)

#### Bottom Panel — Orders / Positions / Trade Tape
```
<BottomPanel collapsible>
  <TabBar>
    <Tab>Open Orders ({count})</Tab>
    <Tab>Positions ({count})</Tab>
    <Tab>Trade Tape</Tab>
    <Tab>Strategy Log</Tab>
  </TabBar>

  <OrdersGrid />         ← AG Grid; Zustand ordersStore; 5s poll
  <PositionsGrid />      ← AG Grid; Zustand positionsStore; 5s poll; P&L in DOM mutation
  <TradeTape />          ← AG Grid; WebSocket events; new rows prepend (limit 200)
  <StrategyLog />        ← LEAN engine signals/log from active forward test
</BottomPanel>
```

---

## 📄 Page 3: Scanner (`/scanner`)

### Layout
```
┌──────────────────────────────────────────────────────────────────────┐
│ HEADER: Scanner — [India ▼] [New Scan +] [Saved Scans ▼] [Alerts ▼] │
├──────────────────────────────────────────────────┬───────────────────┤
│ CRITERIA BUILDER PANEL (left, 380px)             │ RESULTS PANEL     │
│                                                  │ (right, flex)     │
│ Universe: [F&O Stocks ▼]                        │                   │
│                                                  │ Status: RUNNING...│
│ Technical Criteria:                              │ Found: 23 results │
│ ┌─────────────────────────────────────┐         │                   │
│ │ RSI (14)  [ < ▼ ] [ 30 ]  [✕]      │         │ [AG Grid]         │
│ │ Volume    [>2x▼]  [20d avg] [✕]    │         │ Symbol|RSI|Volume │
│ │ [+ Add Technical]                   │         │ |Price|Change     │
│ └─────────────────────────────────────┘         │                   │
│                                                  │ NIFTY     22 5.2M│
│ Options Criteria:                                │ HDFC      28 3.1M│
│ ┌─────────────────────────────────────┐         │ INFOSYS   29 2.8M│
│ │ OI Change [>20%▼] [1d]    [✕]      │         │ ...               │
│ │ IV Pct    [>▼]    [70]    [✕]      │         │                   │
│ │ PCR       [<▼]    [0.7]   [✕]      │         │                   │
│ └─────────────────────────────────────┘         │                   │
│                                                  │ [Create Alert]    │
│ Sort by: [RSI ascending ▼]                      │ [Add to Watchlist]│
│ Limit: [50 results ▼]                           │ [Export CSV]      │
│                                                  │                   │
│ [Run Scan]  [Save as Preset]  [Schedule Alert]  │                   │
└──────────────────────────────────────────────────┴───────────────────┘
│ ACTIVE ALERTS (bottom expandable panel)                               │
│ [Alert list: symbol + condition + status + created + actions]        │
└──────────────────────────────────────────────────────────────────────┘
```

### Components

**CriteriaBuilder**
```
<CriteriaBuilder>
  <UniverseSelector />             ← NSE F&O | NSE All | NSE Indices | US S&P500 | US All | Forex Major
  <TechnicalCriteria>
    <CriterionRow>                 ← Indicator | Operator | Value | Remove button
      <IndicatorSelect />          ← RSI | MACD | BB | SMA | EMA | Volume | Price | ATR | ADX
      <OperatorSelect />           ← < | > | = | crosses above | crosses below | between
      <ValueInput />
    </CriterionRow>
    <AddCriterionButton />
  </TechnicalCriteria>
  <FundamentalCriteria>           ← Market Cap | P/E | EPS | Sector (India + US)
  <OptionsCriteria>               ← OI Change % | IV Percentile | PCR | Max Pain | OI Concentration
  <SortConfig />
  <LimitConfig />
  <RunScanButton />
  <SavePresetButton />
  <ScheduleAlertButton />
</CriteriaBuilder>
```

**Scanner API calls:**
- Run: `POST /api/v1/scanner/run` with full criteria object → returns `scan_id`
- Results: `GET /api/v1/scanner/results/{scan_id}` — polled every 2 seconds until `status: "complete"`
- Save: `POST /api/v1/scanner/presets` with criteria + name
- Load: `GET /api/v1/scanner/presets` → populates Saved Scans dropdown
- Create alert: `POST /api/v1/scanner/alerts` with criteria + frequency (every 15min / hourly / daily)
- Active alerts: `GET /api/v1/scanner/alerts`

**Results Grid (AG Grid)**
- Columns differ by market:
  - India: Symbol | LTP | Change% | RSI | Volume | OI Change | IV | PCR | Sector
  - US: Symbol | LTP | Change% | RSI | Volume | Market Cap | P/E | Beta
  - Forex: Pair | Bid | Ask | Spread | Change% | RSI | ATR | Session
- Right-click context menu: Add to Watchlist | Open Chart | Create Alert | Export Row
- Click row → opens chart in new terminal tab (or navigates to `/terminal?symbol=X`)

---

## 📄 Page 4: Backtest Lab (`/backtest`)

### Layout
```
┌────────────────────────────────────────────────────────────────────────┐
│ HEADER: Backtest Lab — [New Backtest +] [History ▼]                   │
├──────────────────────────────────┬─────────────────────────────────────┤
│ CONFIGURATION PANEL (left 380px) │ RESULTS PANEL (right, flex)        │
│                                  │                                     │
│ Strategy: [SpiderWave ▼]        │ [WAITING FOR BACKTEST]             │
│ Universe:  [India F&O ▼]        │                                     │
│ Start: [2020-01-01]             │ OR (after run):                     │
│ End:   [2024-12-31]             │                                     │
│ Capital: [₹10,00,000]           │ OVERVIEW TAB:                       │
│ Broker: [Dhan ▼]                │ ┌───────────────────────────────┐  │
│                                  │ │ Equity Curve [Recharts Area]  │  │
│ Strategy Parameters:             │ │ vs Benchmark NIFTY            │  │
│ ┌──────────────────────────────┐ │ │ [draggable zoom handle]       │  │
│ │ Fast MA: [10 ↕]              │ │ └───────────────────────────────┘  │
│ │ Slow MA: [30 ↕]              │ │ ┌───────────────────────────────┐  │
│ │ SL %: [2.0 ↕]               │ │ │ Drawdown Chart [red area]     │  │
│ │ TP %: [4.0 ↕]               │ │ └───────────────────────────────┘  │
│ └──────────────────────────────┘ │                                     │
│                                  │ STATISTICS (card grid):             │
│ Resolution: [1min ▼]             │ Sharpe: 1.24 | MaxDD: 12.3%       │
│ Slippage: [0.05% ▼]             │ CAGR: 18.2% | Win Rate: 56%       │
│ Commission: [₹20/trade]          │ Profit Factor: 1.8 | Trades: 312  │
│                                  │ Avg Trade: ₹1,240 | Avg Hold: 2.3d│
│ [Run Backtest]                   │                                     │
│ [Estimate Time: ~4 min]         │ TABS: Overview | Trades | Monthly   │
│                                  │       | Rolling | Insights          │
│ PROGRESS BAR (when running)     │                                     │
│ [=====25%=====] 2020 scanning   │ TRADES TAB: AG Grid, all trades    │
│ Cancel                           │ Entry | Exit | Symbol | P&L | Type  │
│                                  │ Click row → show on chart           │
│ HISTORY (list)                   │                                     │
│ SpiderWave 2024-01-15 ✓          │ MONTHLY TAB: monthly P&L heatmap  │
│ SpiderWave 2024-01-10 ✓          │ Year/month grid, green=profit      │
│ MeanRev   2024-01-08 ✗          │                                     │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### Components

**BacktestConfig**
```
<BacktestConfig>
  <StrategySelector />                ← dropdown of registered strategies from /api/v1/settings/strategies
  <UniverseSelector />
  <DateRangePicker />                 ← shadcn Calendar component
  <CapitalInput />
  <BrokerModelSelector />             ← determines fee model (DhanFeeModel / AlpacaFeeModel / OandaFeeModel)
  <StrategyParamsForm />              ← dynamic: generated from strategy's parameter schema
  <ResolutionSelector />              ← daily | minute | tick
  <SlippageInput />
  <CommissionInput />
  <EstimateTimeButton />              ← GET /api/v1/backtests/estimate with config
  <RunBacktestButton />
</BacktestConfig>
```

**BacktestProgress**
```
<BacktestProgress backtest_id={id}>
  <ProgressBar pct={progress} />      ← progress from WebSocket event: {type: "backtest_progress", pct: 25}
  <StatusLabel />                     ← "Scanning 2021-03-15..."
  <CancelButton />                    ← DELETE /api/v1/backtests/{id}
</BacktestProgress>
```

**BacktestResults** (shown after completion)
```
<BacktestResults result={data}>
  <TabBar tabs={["Overview", "Trades", "Monthly", "Rolling Stats", "Insights"]} />

  <OverviewTab>
    <EquityCurveChart />               ← Recharts AreaChart; equity + drawdown; zoom handle
    <BenchmarkOverlay />               ← NIFTY / SPY overlay based on market
    <DrawdownChart />                  ← red area chart below equity
    <StatisticsGrid>                   ← cards: Sharpe, CAGR, MaxDD, WinRate, ProfitFactor, Trades, AvgTrade
      <StatCard label="Sharpe" value={1.24} good={v > 0.5} />
      <StatCard label="Max Drawdown" value="12.3%" good={v < 20} />
      ...
    </StatisticsGrid>
  </OverviewTab>

  <TradesTab>
    <AG Grid columnDefs={tradeColumns} rowData={trades} />   ← sortable, filterable
    ← click row highlights trade on equity curve
  </TradesTab>

  <MonthlyTab>
    <MonthlyHeatmap data={monthlyPnl} />                     ← D3 or custom grid, green/red cells
  </MonthlyTab>
</BacktestResults>
```

**API calls:**
- Submit: `POST /api/v1/backtests` → `{ backtest_id, estimated_time }`
- Progress: WebSocket event `{ type: "backtest_progress", backtest_id, pct, message }`
- Results: `GET /api/v1/backtests/{id}/results`
- Chart data: `GET /api/v1/backtests/{id}/chart`
- Trade list: `GET /api/v1/backtests/{id}/trades`
- History: `GET /api/v1/backtests` → list for sidebar

---

## 📄 Page 5: Paper Trading Monitor (`/paper`)

### Purpose
Shows a LEAN forward test running in simulation mode with real-time market data but no real orders.

### Layout
```
┌────────────────────────────────────────────────────────────────────────┐
│ HEADER: Paper Trading — [Spider Wave ▼] [Status: 🟢 RUNNING] [Stop]  │
├───────────────────────┬────────────────────────────────────────────────┤
│ STATS BAR (full width)│                                                │
│ Start: ₹10L | Now: ₹11.2L | P&L: +₹1.2L (+12%) | DD: 3.2% | Trades:48│
├───────────────────────┴────────────────────────────────────────────────┤
│ EQUITY CURVE (live, growing chart — Recharts updating every 5 min)    │
│ [Area chart with live data points appending as day progresses]        │
├──────────────────┬─────────────────────────┬──────────────────────────┤
│ OPEN POSITIONS   │ TODAY'S SIGNALS          │ STRATEGY STATE           │
│ [AG Grid]        │ [list of LEAN insights]  │ Regime: TRENDING_BULL   │
│ Symbol|Qty|LTP   │ 09:45 NIFTY BUY signal  │ Wave phase: 3 (impulse) │
│ |Entry|UnrlPnL   │ 10:15 BANKNIFTY signal  │ Capital deployed: 65%   │
│                  │ 13:30 RELIANCE exit      │ Available: 35%          │
├──────────────────┴─────────────────────────┴──────────────────────────┤
│ ORDER HISTORY [AG Grid] — all simulated orders with fill prices       │
├────────────────────────────────────────────────────────────────────────┤
│ LEAN ENGINE LOG (collapsible, last 50 lines)                          │
└────────────────────────────────────────────────────────────────────────┘
```

**Paper vs Live toggle:** dedicated badge in header; paper orders shown in blue not green/red

**API calls:**
- Start: `POST /api/v1/paper/start` with strategy + config
- Stop: `POST /api/v1/paper/stop`
- Status: `GET /api/v1/paper/status` → equity, P&L, DD, trade count
- Positions: `GET /api/v1/paper/positions` every 5s
- Signals: WebSocket event `{ type: "lean_insight", ... }`
- Orders: `GET /api/v1/paper/orders`
- Equity timeline: `GET /api/v1/paper/equity-curve` → data points for chart

---

## 📄 Page 6: Options Chain (`/options`)

### Layout (India mode)
```
┌──────────────────────────────────────────────────────────────────────┐
│ [Symbol: NIFTY ▼] [Expiry: 26-Dec-2024 ▼] [OI Chart] [IV Surface]  │
├──────────────────────────────────────────────────────────────────────┤
│ INFO BAR: Spot: 24,350 | ATM: 24,350 | PCR: 0.82 | Max Pain: 24,200│
│ India VIX: 12.4 | IV Rank: 34% | Total CE OI: 2.3Cr | PE OI: 1.9Cr │
├────────────────────────────────────────────────────────────────────┬─┤
│ OPTIONS CHAIN TABLE (full width)                                   │ │
│                                                                    │ │
│ ← CALLS ─────────────────────── STRIKE ──── PUTS →               │ │
│ OI | Chg OI | IV | Bid | Ask | Strike | Bid | Ask | IV | OI | Chg│ │
│ ─────────────────────────────────────────────────────────────────  │ │
│ 1.2M  +45K  18%  250  251   24,000   ....                        │ │
│ 2.3M  +120K 16%  150  151 ►24,350◄   ← ATM highlighted bold      │ │
│ 1.8M  +30K  15%   80   81   24,400  ...                          │ │
│                                                                    │ │
│ OI bar behind each row: width proportional to OI size             │ │
│ Green OI increase, red OI decrease                                 │ │
│                                                                    │ │
│ Click row → option added to ORDER PANEL on right                  │ │
├────────────────────────────────────────────────────────────────────┤ │
│ OI BAR CHART (below chain, shows OI distribution by strike)       │ │
└────────────────────────────────────────────────────────────────────┴─┘
```

### Tabs (top)
- **Chain** — the option chain table above
- **OI Analysis** — bar chart of OI by strike; call vs put OI; OI change chart
- **IV Surface** — 3D surface using D3.js (strike vs expiry vs IV)
- **Payoff Builder** — build multi-leg strategies; see payoff diagram; calculate Greeks

**Options Chain data API:**
- `GET /api/v1/market/options-chain/NIFTY?expiry=2024-12-26` → full chain with OI, IV, Greeks
- `GET /api/v1/market/options/expiries/NIFTY` → list of available expiries
- WebSocket: subscribe to `{ type: "subscribe_chain", symbol: "NIFTY", expiry: "2024-12-26" }` → OI + bid/ask updates

**India vs US differences:**
- India: OI in lots, PCR displayed, VIX shown, NSE weekly expiry calendar
- US: OI in contracts, Greeks (Delta/Gamma/Theta/Vega) prominent, OPRA data, earnings date shown

---

## 📄 Page 7: Portfolio (`/portfolio`)

### Layout
```
┌──────────────────────────────────────────────────────────────────────┐
│ HEADER: Portfolio — [All Brokers ▼] [Export PDF] [Rebalance →]      │
├───────────────────┬──────────────────────────┬───────────────────────┤
│ SUMMARY CARDS     │ P&L CHART                │ ALLOCATION DONUT      │
│                   │ (Recharts AreaChart)      │ (Recharts PieChart)   │
│ Total Value       │ 30d / 90d / 1y / All     │ By sector             │
│ ₹25,42,000       │ India + US + Forex lines  │ By broker             │
│                   │                          │ By instrument type    │
│ Today P&L         │                          │                       │
│ +₹12,450 (+0.5%) │                          │                       │
│                   │                          │                       │
│ Overall P&L       │                          │                       │
│ +₹4,42,000 (+21%)│                          │                       │
├───────────────────┴──────────────────────────┴───────────────────────┤
│ TABS: Holdings | Algo Positions | Trade History | Risk               │
├────────────────────────────────────────────────────────────────────┤
│ HOLDINGS TABLE (AG Grid)                                           │
│ Symbol | Qty | Avg Cost | LTP | Current Value | P&L | P&L% |       │
│ Days Held | LTCG Eligible | Broker                                  │
│                                                                    │
│ Colour: green rows for profit, red for loss                        │
│ LTCG badge: 🟡 "84 days to LTCG threshold"                        │
└────────────────────────────────────────────────────────────────────┘
```

**API calls:**
- `GET /api/v1/portfolio/holdings` → long-term holdings (equity, ETFs)
- `GET /api/v1/portfolio/positions` → open algo positions (F&O, intraday)
- `GET /api/v1/portfolio/pnl?period=30d` → P&L history for chart
- `GET /api/v1/portfolio/trades?from=&to=` → historical trade list
- `GET /api/v1/portfolio/risk` → VaR, Greeks exposure, correlation

**India-specific:**
- LTCG threshold indicator: days until 1-year mark for each holding
- India tax year: April 1 – March 31 (not calendar year)
- "Rebalance" button → calls PortfolioRebalancer agent via `/api/v1/agents/chat`

---

## 📄 Page 8: AI Agent Hub (`/agents`)

### Purpose
Full-page view of agent sessions, history, and task management. The floating bubble handles quick chat; this page handles history and detailed sessions.

### Layout
```
┌──────────────────────────────────────────────────────────────────────┐
│ HEADER: AI Agent Hub — [New Session +] [Agent Status ●●●○○]         │
├──────────────┬───────────────────────────────────────────────────────┤
│ SESSION LIST │ ACTIVE SESSION                                        │
│ (280px)      │                                                       │
│              │ Session: "Backtest SpiderWave on BankNifty"          │
│ Today        │ Agent: BacktestOrchestrator → OptimizerAgent         │
│ ● Backtest   │ Started: 14:23 | Status: RUNNING                     │
│   14:23      │                                                       │
│   Running    │ CONVERSATION:                                        │
│              │ You: "Run Spider Wave on BankNifty last 3 years..."  │
│ ● Morning    │                                                       │
│   briefing   │ Supervisor: "Routing to BacktestOrchestrator..."     │
│   09:01 Done │                                                       │
│              │ BacktestOrchestrator: "Starting backtest...         │
│ Yesterday    │  Parsing universe: 1 symbol (BANKNIFTY)             │
│ ○ Rebalance  │  Date range: 2022-01-01 to 2024-12-31              │
│   Done       │  Launching LEAN engine..."                           │
│              │                                                       │
│ This Week    │ [LIVE PROGRESS BAR: 45% — scanning 2023...]         │
│ ○ Optimize   │                                                       │
│   Done       │ [Input box at bottom]                               │
│              │ "Optimize further" | "Show me the results" | type...│
└──────────────┴───────────────────────────────────────────────────────┘
│ AGENT STATUS GRID (bottom, always visible)                           │
│ Name | Status | Last Run | Next Run | LLM Used                       │
│ MarketScan | ✅ Done 09:00 | Tomorrow 09:00 | Claude                │
│ RiskGuard  | 🟢 Active | — | Always-on | No LLM                    │
│ RegWatcher | ✅ Done 06:00 | Tomorrow 06:00 | Python only           │
└──────────────────────────────────────────────────────────────────────┘
```

**API calls:**
- `GET /api/v1/agents/sessions` → list sessions
- `GET /api/v1/agents/sessions/{id}` → full conversation history
- `POST /api/v1/agents/chat` with `{session_id, message}` → start/continue session
- `GET /api/v1/agents/status` → all agent statuses
- Streaming: SSE endpoint `/api/v1/agents/chat/stream?session_id={id}` → tokens chunk by chunk

---

## 📄 Page 9: Settings & Broker Config (`/settings`)

### Layout
```
┌──────────────────────────────────────────────────────────────────────┐
│ HEADER: Settings                                                      │
├─────────────────┬────────────────────────────────────────────────────┤
│ SIDEBAR TABS    │ CONTENT AREA                                        │
│                 │                                                     │
│ Connected       │ CONNECTED BROKERS                                   │
│ Brokers         │ ┌──────────────────────────────────────────────┐  │
│                 │ │ Dhan ✅ Connected | Last auth: 2h ago        │  │
│ Strategies      │ │ Account: satyaxxx | Capital: ₹12.4L         │  │
│                 │ │ [Test Connection] [Reconnect] [Remove]       │  │
│ Markets         │ └──────────────────────────────────────────────┘  │
│                 │ ┌──────────────────────────────────────────────┐  │
│ Agents          │ │ Alpaca ✅ Connected | Paper mode             │  │
│ Schedule        │ │ [Switch to Live] [Test] [Remove]             │  │
│                 │ └──────────────────────────────────────────────┘  │
│ Notifications   │ [+ Add Broker]                                     │
│                 │                                                     │
│ About           │ ADD BROKER WIZARD:                                  │
│                 │ Step 1: Choose broker                               │
│                 │ Step 2: Enter API key/secret                        │
│                 │ Step 3: Test connection                             │
│                 │ Step 4: Set as default for market                   │
└─────────────────┴────────────────────────────────────────────────────┘
```

**Settings sections:**
1. **Connected Brokers** — list connected brokers; add/remove; test connection; auth status
2. **Strategies** — list registered strategies; enable/disable; set parameters as defaults
3. **Markets** — toggle India / US / Forex; set default broker per market
4. **Agent Schedule** — when to run each pre-market agent; timezone
5. **Notifications** — alert delivery (in-app / email / Telegram)
6. **About** — version info, LEAN version, licenses

---

## 📄 Page 10: Onboarding (`/onboarding`)

New user flow — only shown once, then skips to dashboard.

```
Step 1: Welcome → "Choose your primary market" (India / US / Both)
Step 2: Connect broker → wizard per market
Step 3: Download LEAN data → progress bar for first data download
Step 4: Run sample backtest → SpiderWave on 3 months of data
Step 5: Done → redirect to /terminal
```

---

## ⚡ The Floating AI Chat Bubble

This component lives in the root layout and persists across ALL pages.

```typescript
// components/ai/AIChatBubble.tsx

const AIChatBubble = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const { activeSymbol, activePage } = useTerminalStore()

  const sendMessage = async () => {
    const context = { page: activePage, symbol: activeSymbol }
    const res = await fetch('/api/v1/agents/chat/stream', {
      method: 'POST',
      body: JSON.stringify({ message: input, context })
    })
    // SSE streaming — append tokens to last message
    const reader = res.body!.getReader()
    // ... token streaming logic
  }

  return (
    <>
      {/* Collapsed: circular button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-blue-600 
                   flex items-center justify-center shadow-xl z-50"
      >
        <BotIcon /> <OnlineDot color="green" />
      </button>

      {/* Expanded: slide-up panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-zinc-900 
                        rounded-2xl shadow-2xl z-50 flex flex-col border border-zinc-700">
          <Header onClose={() => setIsOpen(false)} />
          <MessageList messages={messages} />
          <InputBar onSend={sendMessage} />
        </div>
      )}
    </>
  )
}
```

**Context awareness:** bubble knows what page user is on and what symbol is selected → appends to system prompt. Example: if user is on terminal with NIFTY selected and asks "what's happening?", agent gets context `{ page: "terminal", symbol: "NIFTY", market: "india" }`.

---

## 🔄 Complete Data Flow Architecture

### Tier 1: Hot Data (ticks, 100–200/sec) — Direct DOM Only
```
Broker WS → FastAPI → Redis PUBLISH tick:{symbol}
                         ↓
                   Redis SUBSCRIBE (FastAPI WS manager)
                         ↓
                   FastAPI WebSocket → client
                         ↓
              lib/websocket.ts (singleton class)
                         ↓
              callback(price) → DOM element.textContent = price
                               → CSS class flash added/removed
```

**NEVER does:** `setState`, `useStore.setState`, `useDispatch`

### Tier 2: Medium Data (positions, P&L — every 5 seconds)
```
TanStack Query (background polling, 5000ms interval)
  → GET /api/v1/portfolio/positions
  → Zustand positionsStore.setPositions(data)
  → React components re-render (positions panel)
```

### Tier 3: Cold Data (settings, historical — on demand)
```
TanStack Query (stale-while-revalidate)
  → GET /api/v1/settings/brokers
  → React useState in settings page
```

### Chart Data Flow (most complex)
```
1. Symbol selected → terminalStore.setSymbol("NIFTY")
2. useEffect triggered → fetch historical bars
   GET /api/v1/market/ohlcv/NIFTY?resolution=5min&limit=500
3. klineChart.applyNewData(bars)  ← KLineChart Pro method
4. WebSocket: subscribe to tick:{NIFTY}
5. On each tick:
   wsManager.onTick("NIFTY", tick => {
     klineChart.updateData({ ...lastBar, close: tick.ltp, ... })
     // OR if new bar: klineChart.applyNewData([...bars, newBar])
   })
```

---

## 🗃️ Complete Zustand Store Design

```typescript
// store/terminalStore.ts
interface TerminalStore {
  activeSymbol: string
  activeTimeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w'
  activeMarket: 'india' | 'us' | 'forex'
  activeIndicators: Indicator[]
  watchlist: string[]
  drawings: Record<string, Drawing[]>  // per symbol
  layoutMode: 1 | 2 | 4
  setSymbol: (s: string) => void
  setTimeframe: (t: Timeframe) => void
  setMarket: (m: Market) => void
  addToWatchlist: (s: string) => void
}

// store/positionsStore.ts
interface PositionsStore {
  positions: Position[]                 // open positions
  holdings: Holding[]                   // long-term holdings
  orders: Order[]                       // today's orders
  pnlToday: number
  pnlTotal: number
  lastUpdated: Date
  setPositions: (p: Position[]) => void
  setHoldings: (h: Holding[]) => void
  setOrders: (o: Order[]) => void
}

// store/scannerStore.ts
interface ScannerStore {
  criteria: ScanCriteria
  results: ScanResult[]
  runningScans: Record<string, ScanStatus>
  savedPresets: ScanPreset[]
  alerts: Alert[]
  setCriteria: (c: ScanCriteria) => void
  setResults: (id: string, r: ScanResult[]) => void
}

// store/agentStore.ts
interface AgentStore {
  sessions: AgentSession[]
  activeSessionId: string | null
  agentStatuses: AgentStatus[]
  isBubbleOpen: boolean
  setBubbleOpen: (b: boolean) => void
}

// store/settingsStore.ts  (persisted via zustand/persist to localStorage)
interface SettingsStore {
  connectedBrokers: Broker[]
  defaultBrokerIndia: string
  defaultBrokerUS: string
  defaultBrokerForex: string
  enabledMarkets: Market[]
  notifications: NotificationConfig
}
```

---

## 📡 WebSocket Manager Class

```typescript
// lib/websocket.ts
type TickCallback = (price: number, change: number, changePercent: number) => void

class WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectTimer: number | null = null
  private subscribers = new Map<string, Set<TickCallback>>()
  private reconnectAttempts = 0
  private MAX_RECONNECT = 5

  connect(url: string) {
    this.ws = new WebSocket(url)
    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      // Resubscribe all symbols after reconnect
      const symbols = Array.from(this.subscribers.keys())
      if (symbols.length > 0) {
        this.ws!.send(JSON.stringify({ type: 'subscribe', symbols }))
      }
    }
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === 'tick') {
        this.dispatch(msg.symbol, msg.ltp, msg.change, msg.change_pct)
      }
    }
    this.ws.onclose = () => this.scheduleReconnect(url)
  }

  subscribe(symbol: string, callback: TickCallback): () => void {
    if (!this.subscribers.has(symbol)) {
      this.subscribers.set(symbol, new Set())
      // Send subscribe message to server
      this.ws?.send(JSON.stringify({ type: 'subscribe', symbols: [symbol] }))
    }
    this.subscribers.get(symbol)!.add(callback)
    // Return unsubscribe function
    return () => {
      this.subscribers.get(symbol)!.delete(callback)
      if (this.subscribers.get(symbol)!.size === 0) {
        this.subscribers.delete(symbol)
        this.ws?.send(JSON.stringify({ type: 'unsubscribe', symbols: [symbol] }))
      }
    }
  }

  private dispatch(symbol: string, price: number, change: number, pct: number) {
    this.subscribers.get(symbol)?.forEach(cb => cb(price, change, pct))
  }

  private scheduleReconnect(url: string) {
    if (this.reconnectAttempts < this.MAX_RECONNECT) {
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
      this.reconnectTimer = setTimeout(() => {
        this.reconnectAttempts++
        this.connect(url)
      }, delay) as unknown as number
    }
  }
}

export const wsManager = new WebSocketManager()
```

**Usage in watchlist item:**
```typescript
// components/terminal/WatchlistItem.tsx
const WatchlistItem = ({ symbol }: { symbol: string }) => {
  const ltpRef = useRef<HTMLSpanElement>(null)
  const chgRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const unsubscribe = wsManager.subscribe(symbol, (price, change, pct) => {
      if (!ltpRef.current || !chgRef.current) return
      
      const prevPrice = parseFloat(ltpRef.current.dataset.prev || '0')
      ltpRef.current.dataset.prev = price.toString()
      ltpRef.current.textContent = price.toFixed(2)
      
      // Flash animation
      ltpRef.current.classList.remove('flash-green', 'flash-red')
      ltpRef.current.classList.add(price > prevPrice ? 'flash-green' : 'flash-red')
      setTimeout(() => ltpRef.current?.classList.remove('flash-green', 'flash-red'), 300)
      
      chgRef.current.textContent = `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
      chgRef.current.className = pct >= 0 ? 'text-green-400' : 'text-red-400'
    })
    return unsubscribe
  }, [symbol])

  return (
    <div className="watchlist-item cursor-pointer hover:bg-zinc-800 px-3 py-2">
      <span className="symbol font-medium">{symbol}</span>
      <span ref={ltpRef} data-prev="0" className="ltp tabular-nums">—</span>
      <span ref={chgRef} className="change tabular-nums text-sm">—</span>
    </div>
  )
}
```

---

## 🎨 Design System

### Color Palette (dark theme)
```css
/* Tailwind custom colors in tailwind.config.ts */
background: zinc-950   /* #09090b — main background */
surface: zinc-900      /* #18181b — panels, cards */
border: zinc-800       /* #27272a — dividers */
text-primary: zinc-50  /* #fafafa — primary text */
text-secondary: zinc-400 /* #a1a1aa — labels, secondary */
accent-buy: emerald-400  /* #34d399 — buy, profit, positive */
accent-sell: red-400     /* #f87171 — sell, loss, negative */
accent-blue: blue-500    /* #3b82f6 — buttons, links, accents */
flash-green: bg-emerald-500/30  /* 300ms price flash up */
flash-red: bg-red-500/30        /* 300ms price flash down */
```

### Typography
```
Font: Geist Sans (Next.js default) — clean, professional
Monospace: Geist Mono — prices, quantities, timestamps
Price display: tabular-nums (CSS) — prevents layout shift on digit change
```

### CSS Flash Animation
```css
@keyframes flash-green {
  0% { background-color: rgba(52, 211, 153, 0.4); }
  100% { background-color: transparent; }
}
@keyframes flash-red {
  0% { background-color: rgba(248, 113, 113, 0.4); }
  100% { background-color: transparent; }
}
.flash-green { animation: flash-green 300ms ease-out forwards; }
.flash-red { animation: flash-red 300ms ease-out forwards; }
```

---

## 🔗 Complete API Contract

### Market Data
```
GET  /api/v1/market/status
     → { india: "OPEN|CLOSED|PRE", us: "...", forex: "...", india_close_in: "45m" }

GET  /api/v1/market/quote/{symbol}
     → { symbol, ltp, bid, ask, vol, oi, change, change_pct, high, low, open, prev_close }

GET  /api/v1/market/ohlcv/{symbol}
     ?resolution=1m|5m|15m|1h|4h|1d|1w
     ?limit=500 (default)
     ?from=2024-01-01  (optional, overrides limit)
     ?to=2024-12-31
     → { bars: [{t, o, h, l, c, v}], symbol, resolution }

GET  /api/v1/market/symbols?market=india&q=NIFTY&limit=20
     → { results: [{symbol, name, exchange, type}] }

GET  /api/v1/market/watchlist
     → { symbols: ["NIFTY", "BANKNIFTY", ...] }

POST /api/v1/market/watchlist
     { symbol }

DELETE /api/v1/market/watchlist/{symbol}

GET  /api/v1/market/options-chain/{symbol}?expiry=2024-12-26
     → { calls: [{strike, oi, oi_change, iv, delta, gamma, theta, bid, ask}], puts: [...], spot, atm, pcr }

GET  /api/v1/market/options/expiries/{symbol}
     → { expiries: ["2024-12-26", "2024-12-19", "2024-12-12"] }

GET  /api/v1/market/indices?market=india
     → { indices: [{symbol, ltp, change_pct}] }
```

### Orders
```
POST /api/v1/orders/margin-check
     { symbol, qty, order_type, price, product_type, broker }
     → { required, available, allowed, message }

POST /api/v1/orders
     { symbol, qty, side: buy|sell, order_type, price, trigger_price, product_type, broker }
     → { order_id, status, message }

GET  /api/v1/orders?date=today&status=open|complete|cancelled
     → { orders: [{order_id, symbol, qty, side, type, price, status, time, fill_price}] }

GET  /api/v1/orders/{order_id}
     → { ...full order details }

PUT  /api/v1/orders/{order_id}
     { qty?, price?, trigger_price? }
     → { success, message }

DELETE /api/v1/orders/{order_id}
     → { success, message }
```

### Portfolio
```
GET  /api/v1/portfolio/positions
     → { positions: [{symbol, qty, avg_price, ltp, pnl, pnl_pct, product_type, broker}] }

GET  /api/v1/portfolio/holdings
     → { holdings: [{symbol, qty, avg_price, ltp, value, pnl, pnl_pct, days_held, ltcg_eligible, broker}] }

GET  /api/v1/portfolio/pnl?period=1d|30d|90d|1y|all
     → { history: [{date, value}], today_pnl, total_pnl, total_value }

GET  /api/v1/portfolio/trades?from&to&broker&market
     → { trades: [{date, symbol, qty, side, price, pnl, broker}] }

GET  /api/v1/portfolio/risk
     → { var_95, cvar_95, greeks: {delta, gamma, theta, vega}, correlation_risk }
```

### Backtests
```
POST /api/v1/backtests
     { strategy, universe, start, end, capital, broker_model, params, resolution, slippage, commission }
     → { backtest_id, estimated_minutes }

GET  /api/v1/backtests/{id}
     → { backtest_id, status, progress_pct, message, started_at }

GET  /api/v1/backtests/{id}/results
     → { statistics: {sharpe, max_dd, cagr, win_rate, profit_factor, total_trades, avg_trade},
         equity: [{date, value, benchmark}], drawdown: [{date, value}] }

GET  /api/v1/backtests/{id}/trades
     → { trades: [{entry_time, exit_time, symbol, side, qty, entry_price, exit_price, pnl}] }

GET  /api/v1/backtests/{id}/chart
     → { charts: [{name, series: [{x, y}]}] }

GET  /api/v1/backtests?limit=20&offset=0
     → { backtests: [{backtest_id, strategy, status, sharpe, max_dd, created_at}] }

DELETE /api/v1/backtests/{id}
     → { success }

GET  /api/v1/backtests/estimate
     { strategy, universe, start, end, resolution }
     → { estimated_minutes }
```

### Scanner
```
POST /api/v1/scanner/run
     { universe, criteria: [{type, indicator, operator, value, timeframe}], sort_by, limit }
     → { scan_id }

GET  /api/v1/scanner/results/{scan_id}
     → { status: running|complete|failed, results: [{symbol, values: {rsi, volume, ...}}] }

GET  /api/v1/scanner/presets
     → { presets: [{preset_id, name, criteria}] }

POST /api/v1/scanner/presets
     { name, criteria }
     → { preset_id }

DELETE /api/v1/scanner/presets/{preset_id}

POST /api/v1/scanner/alerts
     { name, criteria, frequency: "15min|1h|1d", notify: "inapp|email" }
     → { alert_id }

GET  /api/v1/scanner/alerts
     → { alerts: [{alert_id, name, status, last_triggered, results_count}] }

DELETE /api/v1/scanner/alerts/{alert_id}
```

### Paper Trading
```
POST /api/v1/paper/start
     { strategy, universe, capital, params }
     → { session_id }

POST /api/v1/paper/stop
     { session_id }

GET  /api/v1/paper/status
     → { status, equity, pnl, pnl_pct, drawdown, trade_count, started_at }

GET  /api/v1/paper/positions
GET  /api/v1/paper/orders
GET  /api/v1/paper/equity-curve
     → { points: [{time, value}] }
```

### Agents
```
POST /api/v1/agents/chat
     { message, session_id?, context?: {page, symbol, market} }
     → { session_id, response, agent_used }

GET  /api/v1/agents/chat/{session_id}
     → { messages: [{role, content, timestamp, agent}] }

GET  /api/v1/agents/chat/stream?session_id={id}
     → SSE stream: data: { type: "chunk", content: "..." } \n\n

GET  /api/v1/agents/sessions
     → { sessions: [{session_id, title, created_at, status}] }

GET  /api/v1/agents/status
     → { agents: [{name, layer, status, last_run, next_run, llm_used}] }

GET  /api/v1/agents/briefing
     → { content: "...", generated_at, agent: "MarketScan" }
```

### Settings & Brokers
```
GET  /api/v1/settings/brokers
     → { brokers: [{broker_id, name, market, status, last_auth}] }

POST /api/v1/settings/brokers
     { broker_type, api_key, api_secret, extra: {} }
     → { broker_id, status }

POST /api/v1/settings/brokers/{id}/test
     → { success, message, latency_ms }

DELETE /api/v1/settings/brokers/{id}

GET  /api/v1/settings/strategies
     → { strategies: [{name, version, status, params_schema}] }

GET  /api/v1/settings/markets
     → { markets: [{market, enabled, default_broker}] }

PUT  /api/v1/settings/markets
     { india: {enabled, default_broker}, us: {...}, forex: {...} }
```

### WebSocket Protocol
```
CLIENT → SERVER:
{ "type": "subscribe", "symbols": ["NIFTY", "BANKNIFTY", "AAPL"] }
{ "type": "unsubscribe", "symbols": ["AAPL"] }
{ "type": "subscribe_chain", "symbol": "NIFTY", "expiry": "2024-12-26" }
{ "type": "subscribe_alerts", "user_id": "..." }

SERVER → CLIENT:
{ "type": "tick", "symbol": "NIFTY", "ltp": 24350.50, "bid": 24349, "ask": 24351, 
  "vol": 1250000, "oi": 8500000, "change": 285.50, "change_pct": 1.19, "ts": 1234567890 }
{ "type": "alert", "alert_id": "...", "symbol": "NIFTY", "message": "RSI below 30", "ts": ... }
{ "type": "backtest_progress", "backtest_id": "...", "pct": 45, "message": "Scanning 2023-03-15" }
{ "type": "lean_insight", "symbol": "NIFTY", "direction": "up", "confidence": 0.74, "ts": ... }
{ "type": "options_update", "symbol": "NIFTY", "expiry": "...", "strike": 24350, 
  "ce_oi": 1200000, "pe_oi": 980000, "ce_iv": 16.5, "pe_iv": 17.2 }
{ "type": "heartbeat", "ts": ... }
```

---

## 🇮🇳 vs 🇺🇸 vs 💱 Market Switching

### What changes when market switches

| Feature | India | US | Forex |
|---------|-------|----|-------|
| Clock display | IST | ET | UTC |
| Currency symbol | ₹ | $ | pair (EUR/USD) |
| Market hours indicator | 9:15–15:30 | 9:30–16:00 ET | 24/5 |
| Order types | MIS / CNC / NRML | Day / GTC / GTD | Market / Limit |
| Lot size display | In lots (Nifty = 25 units) | In shares | In lots (standard) |
| Options chain | OI + PCR + VIX + expiry Thu | Greeks + OPRA + expiry Fri | N/A |
| Indices shown | NIFTY + BANKNIFTY + VIX | SPY + QQQ + VIX (VIX.US) | DXY |
| Scanner defaults | F&O 210 stocks | S&P500 / Russell 2000 | Major pairs |
| P&L currency | ₹ INR | $ USD | pair currency |
| PDT warning | No | Yes (< $25K account) | No |

### Market Switcher Implementation
```typescript
// Zustand terminalStore
const setMarket = (market: Market) => {
  set({ activeMarket: market })
  // All components that depend on market re-render via selector
  // WebSocket resubscribes with new symbol set
  // Chart clears and loads new default symbol
}

// In components, use selector:
const activeMarket = useTerminalStore(s => s.activeMarket)
// Component renders conditionally based on activeMarket
```

---

## 📦 Technology Decisions — Final Library List

| Library | Version | Purpose |
|---------|---------|---------|
| React | 19.x | UI framework |
| Next.js | 15.x (App Router) | SSR, routing, API routes |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 4.x | Utility styling |
| shadcn/ui | latest | UI components (dark mode) |
| @klinecharts/pro | latest | Candlestick charts |
| ag-grid-community | 33.x | Data grids (MIT) |
| recharts | 2.x | Static charts (equity curve, portfolio) |
| d3 | 7.x | Options IV surface, custom viz |
| zustand | 5.x | Client state management |
| @tanstack/react-query | 5.x | Server state, caching, polling |
| react-window | 1.x | Virtualise large lists (watchlist) |
| lucide-react | latest | Icons |
| date-fns | 3.x | Date formatting (IST/ET/UTC) |
| clsx / tailwind-merge | latest | Conditional classes |

---

## 🏗️ Build Sequence (Frontend Phases)

### Phase 7.1 — Foundation (Week 35-36)
- Next.js 15 App Router setup with TypeScript strict
- Tailwind + shadcn/ui dark theme configuration
- Design system: colors, typography, spacing tokens in CSS variables
- Global layout: Navbar + Market Switcher + AI Bubble (collapsed only)
- Route structure: all 10 pages as empty shells
- WebSocket manager class (non-React singleton)
- Zustand store definitions (all stores, empty data)

### Phase 7.2 — Dashboard (Week 36-37)
- Market status bar + clock
- Mini watchlist with WebSocket + direct DOM
- Index tiles with WebSocket
- Open positions mini-grid (AG Grid, Zustand data)
- Sparkline chart (Recharts, REST data)
- AI morning briefing card

### Phase 7.3 — Terminal Chart (Week 37-38)
- KLineChart Pro integration
- Historical bar loading (REST)
- WebSocket live bar update
- Timeframe selector
- Indicator manager
- Drawing tools

### Phase 7.4 — Terminal Watchlist + Order Entry (Week 38-39)
- Full watchlist with search, add/remove
- Symbol search (fuzzy)
- Order form (all fields)
- Margin check flow
- Order confirmation modal
- Market-specific order types (India / US / Forex)

### Phase 7.5 — Terminal Bottom Panel (Week 39)
- Orders grid (AG Grid)
- Positions grid with direct DOM P&L updates
- Trade tape (WebSocket prepend)
- Strategy log

### Phase 7.6 — Scanner (Week 40-41)
- Criteria builder (all criterion types)
- Universe selector
- Run scan + SSE progress
- Results AG Grid
- Save preset + load preset
- Create alert + alert list

### Phase 7.7 — Backtest Lab (Week 41-42)
- Config form + strategy parameter form (dynamic schema)
- Run backtest + WebSocket progress bar
- Equity curve + drawdown (Recharts)
- Statistics cards
- Trades AG Grid
- Monthly P&L heatmap
- History sidebar

### Phase 7.8 — Paper Trading Monitor (Week 42-43)
- Live equity curve (Recharts, appending data)
- Positions + orders grids
- LEAN signal log
- Strategy state panel

### Phase 7.9 — Options Chain (Week 43-44)
- Options chain table (AG Grid, OI bars)
- Expiry selector
- WebSocket OI updates
- OI bar chart (Recharts)
- IV Surface (D3.js — most complex component)
- Payoff builder

### Phase 7.10 — Portfolio (Week 44-45)
- Holdings AG Grid with LTCG indicator
- P&L chart (Recharts)
- Allocation donut chart (Recharts)
- Risk metrics panel

### Phase 7.11 — AI Agent Hub (Week 45)
- Full session chat UI
- SSE token streaming display
- Session list sidebar
- Agent status grid

### Phase 7.12 — Settings + Onboarding (Week 45-46)
- Broker connection wizard (multi-step)
- Strategy management
- Market toggles
- Notification settings
- Onboarding flow (first launch only)

### Phase 7.13 — Polish + Performance (Week 46)
- Bundle splitting: each page as dynamic import
- Performance audit: Chrome DevTools, no unnecessary renders
- CSS flash animation tuning
- Keyboard shortcuts (K for search, B for buy, S for sell, ESC to close)
- Error boundaries on all panels
- Empty states for all grids
- Loading skeletons for all REST-loaded panels

---

## ⚠️ Performance Rules — Non-Negotiable

```
Rule 1: NEVER call setState or useStore.setState inside a WebSocket onmessage handler
        for price data. Use direct DOM mutation via refs.

Rule 2: NEVER render a component inside a WebSocket callback.

Rule 3: ALL AG Grid tables that show live P&L must use cell renderer that touches
        DOM directly (cellRenderer using plain JS, not React renderer for hot cells).

Rule 4: Chart live updates use klineChart.updateData() — NOT re-rendering the chart component.

Rule 5: Watchlist must be virtualised (react-window) if > 50 symbols.

Rule 6: The AI chat bubble animation (slide-up) must use CSS transform, not layout.

Rule 7: Backtest equity curve uses Recharts (static, REST data). Never WebSocket for charts.

Rule 8: WebSocket connects once on app load. Never create multiple WebSocket instances.

Rule 9: TanStack Query for all REST polling. Never use useEffect + setInterval for data fetching.

Rule 10: All pages are lazy-loaded (Next.js dynamic import). Only the terminal page
         is preloaded on dashboard hover.
```

---

*This blueprint covers every page, every component, every API endpoint, every data flow, and every performance rule. A developer can start building from Phase 7.1 without asking any questions.*
