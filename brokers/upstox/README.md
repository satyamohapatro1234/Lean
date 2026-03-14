# upstox Broker Integration

**Status: Phase 5**

Free API (no monthly subscription). WebSocket uses Protobuf encoding (efficient). Good for testing without broker API costs.

## Planned Files

```
brokers/upstox/
├── client.py      - Broker client (auth, token refresh)
├── websocket.py   - Live tick streaming to Redis pub/sub
├── orders.py      - Order placement and modification
└── historical.py  - Historical data fetcher
```

All brokers implement the same interface. The strategy engine never knows which broker is active.
