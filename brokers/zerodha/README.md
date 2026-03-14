# zerodha Broker Integration

**Status: Phase 5**

Most mature Indian broker API. KiteConnect Python SDK. Built-in WebSocket auto-reconnect. Offers basket margin API for accurate pre-order margin check (free).

## Planned Files

```
brokers/zerodha/
├── client.py      - Broker client (auth, token refresh)
├── websocket.py   - Live tick streaming to Redis pub/sub
├── orders.py      - Order placement and modification
└── historical.py  - Historical data fetcher
```

All brokers implement the same interface. The strategy engine never knows which broker is active.
