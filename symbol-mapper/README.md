# Symbol Mapper

Bidirectional mapping between broker instrument IDs and LEAN Symbol objects.

## Problem

Every broker uses a different identifier:
- Dhan: integer `security_id` (e.g., `49581`)
- Zerodha: integer `instrument_token` (e.g., `10742530`)
- Upstox: string `instrument_key` (e.g., `NSE_FO|58442`)
- Angel One: string `token` (e.g., `58442`)
- LEAN: `Symbol` object with ticker, market, security type, expiry, strike, right

## The Mapper

`universal_mapper.py` implements LEAN's `ISymbolMapper` interface:
- `get_lean_symbol(broker, broker_id)` → LEAN Symbol
- `get_broker_id(lean_symbol, broker)` → broker-specific ID
- `round_trip_test(symbol, broker)` → verify both directions work

All lookups go through the SQLite instrument master database.

## Critical Edge Cases

- **Options expiry dates**: Always use broker's actual expiry from instrument master. Never calculate from calendar. NSE has non-standard expiry dates.
- **Lot size changes**: Get lot size from `lot_size_history` table using trade date, not a fixed value.
- **Symbol changes**: Companies rename symbols. MapFiles in LEAN handle this for backtesting.

## Usage

```python
from symbol_mapper.universal_mapper import UniversalMapper

mapper = UniversalMapper(db_path="instrument-master/instruments.db")

# Dhan security_id → LEAN Symbol
lean_sym = mapper.get_lean_symbol("dhan", "49581")

# LEAN Symbol → Dhan security_id  
dhan_id = mapper.get_broker_id(lean_sym, "dhan")

# Round-trip test
assert mapper.round_trip_test("NIFTY", "dhan")
```
