# Frontend — React Trading Terminal

**Status: Phase 7 (11 sub-phases)**

Professional trading terminal built with React + TypeScript + Next.js.

## The Critical Architecture Insight

> Putting live tick prices into React state causes 200 re-renders/second. At 200 symbols updating during market hours, the UI becomes completely unusable. This is why most trading terminal frontend builds fail.

**Solution: Three data speed tiers with different update mechanisms:**

| Data Type | Update Speed | Mechanism |
|-----------|-------------|-----------|
| Tick prices | 100–200/sec | Direct DOM mutation (NO React state) |
| Positions, P&L | Every 5 seconds | Zustand + REST polling |
| Settings, config | User-driven | Normal React state |

The WebSocket connection lives as a singleton manager OUTSIDE React. Price cells register callbacks with the manager. When a tick arrives, the manager calls those callbacks directly, which update `element.textContent` without any React render cycle.

## Technology Stack

| Component | Library | License |
|-----------|---------|---------|
| Framework | Next.js 14 + TypeScript | MIT |
| Styling | Tailwind CSS + shadcn/ui | MIT |
| Trading chart | KLineChart Pro | Apache 2.0 |
| Data grids | AG Grid Community | MIT |
| Analytics charts | Recharts | MIT |
| Options viz | D3.js | BSD |
| State (medium) | Zustand | MIT |
| Data fetching | TanStack Query | MIT |
| Component dev | Storybook | MIT |

## 11 Sub-Phases

| Sub-Phase | What Gets Built |
|-----------|----------------|
| 7.1 | Design system (Tailwind tokens, shadcn, Storybook) |
| 7.2 | Layout shell (3-panel terminal, no real data) |
| 7.3 | Performance architecture (hot/medium/cold data flows) |
| 7.4 | Watchlist (direct DOM mutation, price flash animation) |
| 7.5 | KLineChart Pro (historical load + streaming WebSocket) |
| 7.6 | Order entry (margin check → confirmation → execute) |
| 7.7 | Positions + orders (AG Grid, live P&L update) |
| 7.8 | Backtest results (Recharts equity curve, AlgoLoop tabs) |
| 7.9 | Options chain (D3.js IV heatmap + payoff graph) |
| 7.10 | AI assistant panel (LangGraph agent chat) |
| 7.11 | Settings + configuration |

## Folder Structure (to be populated in Phase 7)

```
frontend/
├── components/
│   ├── watchlist/       ← WatchlistPanel, WatchlistRow (direct DOM)
│   ├── chart/           ← KLineChartWrapper, IndicatorSelector
│   ├── orders/          ← OrderEntryPanel, OrderBook, PositionsTable
│   ├── backtest/        ← EquityCurve, TradesList, BacktestStats
│   ├── options/         ← OptionChain, IVSurface, PayoffGraph
│   ├── agents/          ← AIAssistantPanel, AgentResponse
│   └── ui/              ← Design system components (shadcn)
├── hooks/
│   ├── useWebSocket.ts  ← Singleton WebSocket manager
│   ├── useMarketData.ts ← Price subscription hook
│   └── usePositions.ts  ← Position polling hook
├── pages/               ← Next.js App Router pages
├── lib/
│   ├── websocket.ts     ← WebSocket singleton (outside React)
│   ├── api.ts           ← REST API client
│   └── store.ts         ← Zustand stores
└── stories/             ← Storybook stories for every component
```

## Starting Phase 7

Phase 7 only starts after the FastAPI backend (Phase 3) is complete. The frontend is useless without:
- WebSocket endpoint for live data
- REST endpoints for historical data
- Order API for trade execution
- Backtest API for strategy results
