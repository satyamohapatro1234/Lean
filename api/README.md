# FastAPI Backend

**Status: Phase 3**

REST API + WebSocket server powering the React trading terminal.

## Endpoint Groups

### Data
- `GET /api/ohlcv/{symbol}?from=&to=&interval=` — Historical OHLCV from QuestDB
- `GET /api/symbols/search?q=` — Instrument master search
- `GET /api/option-chain/{symbol}?expiry=` — Live option chain

### Backtest
- `POST /api/backtest/run` — Launch LEAN backtest (async, returns job_id)
- `GET /api/backtest/{job_id}/status` — Poll job status
- `GET /api/backtest/{job_id}/result` — Get full backtest result JSON

### Live Trading
- `GET /api/positions` — Current open positions from broker
- `GET /api/orders` — Today's order list
- `POST /api/orders` — Place new order (with pre-margin-check)
- `PUT /api/orders/{id}` — Modify pending order
- `DELETE /api/orders/{id}` — Cancel pending order
- `GET /api/portfolio/margin` — Current margin usage

### Agents
- `POST /api/agents/query` — Send message to agent, returns async job
- `GET /api/agents/{job_id}` — Poll agent response

### WebSocket
- `WS /ws` — Live tick stream (subscribe to symbols after connect)

## WebSocket Protocol

```json
// Subscribe
{"action": "subscribe", "symbols": ["NIFTY", "BANKNIFTY", "RELIANCE"]}

// Server pushes ticks
{"type": "tick", "symbol": "NIFTY", "ltp": 24350.50, "bid": 24350.0, "ask": 24351.0, "ts": 1741234567890}

// Server pushes minute bar close  
{"type": "bar", "symbol": "NIFTY", "open": 24340.0, "high": 24360.0, "low": 24335.0, "close": 24350.50, "volume": 12430, "ts": 1741234560000}
```
