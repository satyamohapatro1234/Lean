# Spider Wave MTF Strategy

Multi-timeframe wave strategy for NSE F&O, implementing Narang's 4-component framework inside LEAN.

## Strategy Overview

The Spider Wave system analyses price action across three time horizons:
- **Grandmother Wave**: Weekly/Monthly — institutional trend direction
- **Mother Wave**: Daily — intermediate trend direction  
- **Son Wave**: Intraday (15min/1hr) — entry/exit timing

A trade signal requires alignment across all three timeframes.

## 4-Component Implementation (Narang)

### Alpha Model (`alpha_model.py`)
Reads LEAN price data, computes wave signals, emits `Insight` objects:
- Direction: `InsightDirection.Up` or `InsightDirection.Down`
- Confidence: 0.0–1.0 (maps to Carver's −20 to +20 forecast scale)
- Duration: Based on wave timeframe (longer for Grandmother signals)

### Risk Model (LEAN built-in)
- `MaximumDrawdownPercentPortfolio(0.05)` — 5% portfolio hard stop
- `MaximumDrawdownPercentPerSecurity(0.03)` — 3% per-position hard stop

### Portfolio Construction (LEAN built-in)
- `RiskParityPortfolioConstructionModel` — Hierarchical Risk Parity
- Validated by López de Prado (2020): beats Markowitz out-of-sample

### Execution Model (LEAN built-in)
- `VolumeWeightedAveragePriceExecutionModel` — minimises market impact
- Validated by Barry Johnson's *Algorithmic Trading & DMA*

## Validation Gates (Davey + López de Prado)

All 5 gates must pass before live deployment:
1. In-Sample Backtest (2019–2021, optimized)
2. Walk Forward Optimization (rolling windows)
3. Monte Carlo Robustness (10,000 shuffles, 95% positive Sharpe)
4. CPCV — Combinatorial Purged Cross-Validation (non-IID aware)
5. Out-of-Sample (2022–2024, never touched)

## Files

| File | Purpose |
|------|---------|
| `alpha_model.py` | Spider MTF wave detection → LEAN Insight objects |
| `fee_model.py` | DhanFeeModel with versioned STT (pre/post Oct 2024) |
| `main.py` | Full LEAN algorithm wiring all 4 components |

## Running

```bash
# Backtest with default parameters
python run_backtest.py --strategy spider-wave --from 2022-01-01 --to 2024-01-01

# Euler optimization
python run_backtest.py --strategy spider-wave --optimize euler --from 2019-01-01 --to 2021-12-31

# Monte Carlo validation
python validate.py --strategy spider-wave --runs 10000
```
