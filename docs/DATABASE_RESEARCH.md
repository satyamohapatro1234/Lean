# Time-Series Database Research — QuestDB Selected

## Benchmark Results (2025)

| Database | OHLCV aggregation | Ingestion speed | Use case |
|----------|------------------|-----------------|----------|
| QuestDB  | 25ms             | 1.4M rows/sec   | Financial tick data, real-time |
| ClickHouse | 547ms          | 914K rows/sec   | Analytics at massive scale |
| TimescaleDB | 1,021ms       | 145K rows/sec   | PostgreSQL ecosystem |
| PostgreSQL | 3,493ms        | ~50K rows/sec   | General purpose |

## Why QuestDB for Our Platform

1. Founded by ex-low-latency trading engineers — designed for financial data
2. Time-based array storage model — exactly how tick data is structured
3. Fastest ingestion for our use case (tick data = append-only, time-ordered)
4. Fastest queries for OHLCV aggregation (our most common query pattern)
5. Open source (Apache 2.0)
6. PostgreSQL wire protocol — existing SQL tools work
7. Native WebSocket ingestion API
8. Used by: Deutsche Bank, Toggle.ai, Aquis Exchange (real trading companies)

## QuestDB Schema for Our Platform

```sql
-- Live tick storage
CREATE TABLE ticks (
    timestamp TIMESTAMP,
    symbol SYMBOL CAPACITY 5000,
    price DOUBLE,
    volume LONG,
    bid DOUBLE,
    ask DOUBLE,
    oi LONG
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- OHLCV bars (generated from ticks)
CREATE TABLE ohlcv (
    timestamp TIMESTAMP,
    symbol SYMBOL CAPACITY 5000,
    timeframe SYMBOL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY MONTH;

-- Option chain snapshots
CREATE TABLE option_chain (
    timestamp TIMESTAMP,
    underlying SYMBOL,
    strike DOUBLE,
    expiry TIMESTAMP,
    ce_price DOUBLE,
    pe_price DOUBLE,
    ce_oi LONG,
    pe_oi LONG,
    ce_iv DOUBLE,
    pe_iv DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

## Architecture Decision

```
Broker WebSocket → QuestDB (direct ILP protocol ingestion)
                ↓
         Redis pub/sub (broadcast to multiple WebSocket subscribers)
                ↓
         Frontend WebSocket clients (KLineChart real-time updates)

QuestDB → LEAN /Data folder export (for backtesting)
```

