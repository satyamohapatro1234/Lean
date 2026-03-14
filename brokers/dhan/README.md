# Dhan Broker Integration

**Status: Phase 0–2 (first broker)**

Dhan is the first broker because it provides historical options OHLCV + Open Interest data, which is rare among Indian brokers and required for our options backtesting.

## Rate Limits (Official Dhan Docs)

| API | Limit |
|-----|-------|
| Historical data (intraday) | 20 req/sec |
| Option Chain | 1 req per 3 seconds |
| Order placement | 25 orders/sec, 250 orders/min |
| Market Quote (batch) | 1 req for up to 1000 instruments |
| Intraday window | 90 days per request |
| Daily data | From stock inception date |

**We use 8 req/sec** for historical downloads (max is 20, we use 8 for safety).

## API Cost

- Trading API: Free
- Data API: Free if 25 F&O trades/month, otherwise Rs 499/month
- No extra charges for API usage

## Token Management

Dhan tokens expire every 24 hours (SEBI requirement). The automated refresh:
1. Runs at 6 AM daily via cron
2. Uses Playwright to log into web portal
3. Completes TOTP 2FA automatically
4. Extracts and saves new access token
5. On failure: sends alert + halts trading for the day

## Key Features

- Historical options OHLCV + OI (up to 5 years)
- Live option chain with Greeks and OI
- WebSocket for 1000 instruments per connection
- 20-level market depth (Level 3 data)
- Super Orders: entry + target + trailing SL in one order

## Files (to be created in Phase 0–2)

```
brokers/dhan/
├── client.py          ← DhanClient wrapper (auth, token refresh)
├── websocket.py       ← DhanWebSocket (live ticks → Redis pub/sub)
├── orders.py          ← Order placement, modification, cancellation
├── historical.py      ← Historical data fetcher (used by intraday_downloader)
└── option_chain.py    ← Option chain fetcher (live + historical)
```
