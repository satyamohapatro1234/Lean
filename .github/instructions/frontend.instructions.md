---
applyTo: "frontend/**"
---

# Frontend Instructions

CRITICAL: Tick prices must NEVER update React state. This causes 200 renders/second and freezes the browser.

The correct pattern:
- `lib/websocket.ts` is a CLASS (singleton, not a React component)
- Price cells register a callback: `wsManager.subscribe(symbol, (price) => { el.textContent = price })`
- The callback updates the DOM directly — no React setState, no Zustand

Data tiers:
- Tick prices (100–200/sec): Direct DOM mutation via WebSocket singleton callbacks
- Positions/P&L (every 5 sec): Zustand store + REST polling
- Settings/config: Normal React state (re-renders fine at human speed)

Chart library: KLineChart Pro (@klinecharts/pro) — Apache 2.0, drawing tools, indicators included.
Do NOT use TradingView Lightweight Charts (no indicators, no drawing tools).

Build sub-phases in strict order: 7.1 → 7.2 → 7.3 → 7.4 → 7.5 → 7.6 → 7.7 → 7.8 → 7.9 → 7.10 → 7.11
Do NOT start Phase 7 until Phase 3 (FastAPI backend) is complete.
