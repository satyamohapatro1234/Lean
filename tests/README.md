# Tests

## Test Philosophy

Every component that touches money must be tested. The test suite validates:
- Data quality (no bad prices reach the strategy)
- Symbol mapping round-trips (Dhan ID ↔ LEAN Symbol)
- Fee model accuracy (calculated fee matches actual Dhan contract note)
- LEAN data format correctness (prices × 10000, millisecond timestamps)
- Bhavcopy parsing (all 2000+ symbols loaded correctly)

## Test Files (Phase 0 targets)

| Test | What It Validates |
|------|------------------|
| `test_schema.py` | SQLite schema creates correctly, constraints work |
| `test_symbol_mapper.py` | Round-trip: Dhan ID → LEAN → Dhan ID for 20 instruments |
| `test_fee_model.py` | Fee calculation matches Dhan rates pre/post Oct 2024 |
| `test_bhavcopy.py` | Bhavcopy parser handles all NSE equity formats |
| `test_data_quality.py` | No gaps, no outliers, no zero-volume trading days |
| `test_lean_format.py` | LEAN zip format readable by LEAN engine |
| `test_lot_size.py` | Correct lot size returned for pre/post Dec 2024 dates |

## Running Tests

```bash
# All tests
pytest tests/ -v

# Just Phase 0 tests
pytest tests/test_schema.py tests/test_symbol_mapper.py tests/test_fee_model.py -v

# Data quality check (run after every download)
pytest tests/test_data_quality.py -v --symbol NIFTY --from 2023-01-01
```
