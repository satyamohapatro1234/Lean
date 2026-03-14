# angelone Broker Integration

**Status: Phase 5**

SmartAPI with margin calculator. Historical data available. WebSocket for live feeds.

## Planned Files

```
brokers/angelone/
├── client.py      - Broker client (auth, token refresh)
├── websocket.py   - Live tick streaming to Redis pub/sub
├── orders.py      - Order placement and modification
└── historical.py  - Historical data fetcher
```

All brokers implement the same interface. The strategy engine never knows which broker is active.
