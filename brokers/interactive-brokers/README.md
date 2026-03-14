# interactive-brokers Broker Integration

**Status: Phase 6**

Global markets: US equities, US options, European futures (Eurex), Forex, Crypto. LEAN has built-in IBBrokerageModel. Uses ib_insync Python library.

## Planned Files

```
brokers/interactive-brokers/
├── client.py      - Broker client (auth, token refresh)
├── websocket.py   - Live tick streaming to Redis pub/sub
├── orders.py      - Order placement and modification
└── historical.py  - Historical data fetcher
```

All brokers implement the same interface. The strategy engine never knows which broker is active.
