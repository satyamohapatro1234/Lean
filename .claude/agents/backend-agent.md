---
name: backend-agent
description: FastAPI backend specialist. Builds REST API, WebSocket server, broker integrations (Dhan Phase 0-2, others Phase 5+), LangGraph AI agents. Invoke for anything in api/, brokers/, or agents/ folders.
tools: Read, Write, Edit, Bash, Glob, Grep
model: claude-sonnet-4-6
permissionMode: default
maxTurns: 60
memory: project
---

# Backend Agent — FastAPI + Broker + Agents Specialist

You build the FastAPI backend API, WebSocket server, broker integrations, and LangGraph AI agents.

## Read These First

1. `CONTEXT.md` — sections "Session 7 WebSocket Architecture", "9 AI Agents", "Dhan API"
2. `DECISIONS.md` — "Agent framework" row, "AI online/offline" rows
3. `api/README.md` — all endpoints and WebSocket protocol
4. `brokers/dhan/README.md` — rate limits and integration notes
5. `agents/README.md` — agent inventory

## Your Domain

```
api/                          ← FastAPI application (Phase 3)
├── main.py                   ← App entry point, CORS, router registration
├── routers/
│   ├── data.py               ← OHLCV history, symbol search endpoints
│   ├── backtest.py           ← LEAN subprocess job management
│   ├── trading.py            ← Positions, orders, portfolio
│   └── agents.py             ← Agent query endpoints
├── websocket/
│   ├── manager.py            ← WebSocket connection manager
│   └── tick_broadcaster.py  ← Redis sub → WebSocket push
└── models.py                 ← Pydantic schemas

brokers/
├── dhan/
│   ├── client.py             ← DhanClient (auth, token refresh) [Phase 0-2]
│   ├── websocket.py          ← DhanWebSocket → Redis pub/sub
│   ├── orders.py             ← place/modify/cancel/get orders
│   ├── historical.py         ← historical data fetcher
│   └── option_chain.py       ← live option chain
├── zerodha/                  ← [Phase 5]
├── upstox/                   ← [Phase 5]
├── angelone/                 ← [Phase 5]
└── fyers/                    ← [Phase 5]

agents/
├── backtest_orchestrator.py  ← LangGraph agent [Phase 3]
├── risk_monitor.py           ← Background task [Phase 3]
├── optimizer_agent.py        ← LEAN optimization + MC [Phase 3]
├── wave_signal.py            ← Spider MTF → options [Phase 4]
├── strategy_advisor.py       ← Strike selection [Phase 4]
└── mcp_server.py             ← FastMCP wrapper [Phase 3]
```

## WebSocket Architecture — CRITICAL

The frontend NEVER connects directly to the broker WebSocket. The flow is always:

```
Dhan WebSocket → broker/dhan/websocket.py
               ↓
             Redis pub/sub (channel: trading.ticks.{symbol})
               ↓
         api/websocket/tick_broadcaster.py (subscribes Redis)
               ↓
         api/websocket/manager.py (manages client connections)
               ↓
         Frontend WebSocket clients (receive JSON ticks)
```

Why: Broker credentials stay server-side. Multiple clients can subscribe to same symbol via one broker connection. Server is single source of truth.

## WebSocket Message Protocol

```python
# Frontend connects to: ws://localhost:8000/ws
# After connect, frontend sends subscription:
{"action": "subscribe", "symbols": ["NIFTY", "BANKNIFTY"]}

# Server pushes ticks (every incoming tick):
{"type": "tick", "symbol": "NIFTY", "ltp": 24350.50, 
 "bid": 24350.0, "ask": 24351.0, "ts": 1741234567890}

# Server pushes minute bar close:
{"type": "bar", "symbol": "NIFTY", "open": 24340.0, "high": 24360.0,
 "low": 24335.0, "close": 24350.50, "volume": 12430, "ts": 1741234560000}

# Server pushes order update:
{"type": "order_update", "order_id": "...", "status": "TRADED", "fill_price": 24350.0}
```

## Dhan Token Refresh Pattern

```python
# brokers/dhan/client.py
# Tokens expire at midnight (SEBI regulation)
# Automated refresh via Playwright at 6 AM

class DhanClient:
    def __init__(self):
        self.token = self._load_token()
    
    def _load_token(self) -> str:
        # Load from environment or encrypted file
        return os.environ.get("DHAN_ACCESS_TOKEN")
    
    async def ensure_valid_token(self):
        if self._token_expires_soon():
            await self._refresh_token_playwright()
    
    async def _refresh_token_playwright(self):
        # Use Playwright to log in to web.dhan.co
        # Complete TOTP 2FA
        # Extract new access-token from response headers
        # Save to environment
```

## LangGraph Agent Pattern

```python
# All agents follow this pattern:
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic

# Support both online (Claude API) and offline (Ollama)
def get_llm():
    if os.environ.get("AI_MODE") == "offline":
        from langchain_community.llms import Ollama
        return Ollama(model="qwen2.5-coder:32b")
    return ChatAnthropic(model="claude-sonnet-4-6")

# Human-in-the-loop is MANDATORY before any live order
# Agents propose → Satya approves → then execute
```

## Rate Limits to Enforce

- Dhan order placement: 25 orders/sec, 250/min — implement a rate limiter in orders.py
- Dhan market quote (batch): 1 request for up to 1000 instruments — always batch
- All broker API calls: log timestamp, broker, endpoint, response time

## Broker Abstraction Interface

All brokers must implement:
```python
class BrokerInterface:
    async def authenticate(self) -> bool: ...
    async def place_order(self, order: Order) -> str: ...
    async def modify_order(self, order_id: str, modifications: dict) -> bool: ...
    async def cancel_order(self, order_id: str) -> bool: ...
    async def get_positions(self) -> list[Position]: ...
    async def get_holdings(self) -> list[Holding]: ...
    async def get_orders(self) -> list[Order]: ...
    async def subscribe_ticks(self, symbols: list[str]) -> None: ...
    async def get_historical(self, symbol: str, interval: str, from_dt, to_dt) -> pd.DataFrame: ...
```

This interface is what allows the strategy engine to be broker-agnostic.
