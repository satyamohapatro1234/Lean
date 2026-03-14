# fyers Broker Integration

**Status: Phase 5**

Options chain data and historical data similar to Dhan. Free data access.

## Planned Files

```
brokers/fyers/
├── client.py      - Broker client (auth, token refresh)
├── websocket.py   - Live tick streaming to Redis pub/sub
├── orders.py      - Order placement and modification
└── historical.py  - Historical data fetcher
```

All brokers implement the same interface. The strategy engine never knows which broker is active.
