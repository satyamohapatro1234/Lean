# Spider MTF Wave System v5.0 — LEAN Python

Faithful conversion of `Spider_MTF_v5.0` Pine Script v6 → QuantConnect LEAN Python.

---

## Strategy Logic (unchanged from Pine Script)

### Wave Hierarchy
| Layer | Timeframe | Purpose |
|-------|-----------|---------|
| Grandmother | Quarterly | Macro trend gating (4-condition score 0–4) |
| Mother | Monthly | Trend validity + range filter |
| Macro Wave | Monthly H/L | Position within monthly range |
| Son Wave | 4-Week H/L | Weekly sub-structure |
| Trigger | 6-Hour | Entry confirmation candles |

### Entry Types
| Signal | Condition |
|--------|-----------|
| **A — Macro Breakout** | Price closes above Monthly High (2-candle + retest + vol sequence) |
| **B — Overshot Reversal** | Price was below Monthly Low, bounces back inside |
| **C — Son Breakout** | Weekly High break while in monthly Supply zone |
| **D — Son Bottom** | Weekly Low bounce in Supply or Bottom zone |

### 5 Trap Elimination Rules
| Rule | Condition |
|------|-----------|
| 1 | Two consecutive 6H candles close above the level (no single-bar fakeout) |
| 2 | Price pulled back to the broken level and held above it (retest + hold) |
| 3 | Volume sequence: build → surge → sustain across 3 bars |
| 4 | Entry candle closes in top 30% of range + clean upper wick |
| 5 | Not in last 30 minutes of NSE session (15:00–15:30 IST) |

### Exit Logic
| Exit | Trigger |
|------|---------|
| Hard Stop | `close < entry_price - ATR × stop_mult` (after min hold) |
| Partial 50% | `high >= Monthly High + Monthly Range × 0.272` (Fib 1.272) |
| Full Exit | `high >= Monthly High + Monthly Range × 0.618` (Fib 1.618) |
| Trail Stop | Chandelier: `trail_high - ATR × trail_mult` (after min hold) |
| Structure Break | `close < Monthly Low` (after min hold) |

---

## Implementation Notes

### NSE 6H Bar = 1 Trading Day
NSE trading hours are 9:15–15:30 IST (6 hours 15 minutes). This means there is
essentially **one 6H bar per trading day**. So:
- "Two-candle confirmation" = two consecutive daily closes above the level
- Signal fires at the open of the following trading day
- The time filter (Rule 5) always passes in backtesting since we act at day-open

### Python Version Constraint
LEAN's bundled `pythonnet 2.0.53` requires **Python 3.11 or earlier**.
Always activate `.venv311` before running:

```bash
.venv311\Scripts\activate   # Windows
source .venv311/bin/activate # Linux/Mac
```

### Running the Backtest

```bash
# Using the engine wrapper (recommended)
python engine-wrapper/run_backtest.py --config strategies/spider_wave/lean-config.json

# Or directly
cd engine/Lean
PYTHONNET_PYDLL=python311.dll \
  dotnet run --project Launcher \
  --configuration Release \
  -- --config ../../strategies/spider_wave/lean-config.json
```

### Changing the Symbol
Edit `strategies/spider_wave/lean-config.json`:
```json
"parameters": {
    "symbol": "RELIANCE"
}
```
Or pass via command line:
```bash
python engine-wrapper/run_backtest.py --symbol RELIANCE
```

### Parameter Optimization
The `lean-config.json` parameters can be optimized using LEAN's built-in optimizer.
Key parameters to sweep:
- `risk_pct`: 0.5 to 2.0 (step 0.25)
- `atr_mult_norm`: 1.0 to 2.5 (step 0.25)
- `atr_mult_trail`: 1.5 to 3.0 (step 0.25)

---

## Data Requirements

Before running, ensure the data pipeline has populated `lean-data/` with:
```
lean-data/equity/india/minute/{symbol}/{YYYYMMDD}_trade.zip
```

Run the data pipeline (Phase 0.3–0.5):
```bash
python platform/data-pipeline/india/bhavcopy_downloader.py
python platform/data-pipeline/india/lean_writer.py
```

---

## Files

| File | Purpose |
|------|---------|
| `main.py` | Complete LEAN Python algorithm |
| `lean-config.json` | LEAN configuration for this strategy |
| `README.md` | This file |

**TODO (Phase 1):**
- `fee_model.py` — `DhanFeeModel` implementing `IFeeModel`
  - STT: 0.1% post-Oct 2024, 0.0625% pre-Oct 2024 (date-aware)
  - Exchange charge: NSE 0.035% for F&O
  - SEBI charge: ₹10 per crore
  - GST on brokerage: 18%
  - Stamp duty: 0.015% for delivery
