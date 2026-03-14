---
applyTo: "strategies/**,symbol-mapper/**,run_backtest.py,validate.py"
---

# Strategy and LEAN Instructions

You are working with QuantConnect LEAN engine code.

LEAN is C#. Python algorithms run inside LEAN via Python.NET bridge.
External communication is ONLY via subprocess: write config.json → run Docker → read result.json.
Never try to import LEAN as a Python package.

The strategy MUST implement Narang's 4 components (all mandatory):
1. AlphaModel (Spider Wave → Insights)
2. RiskManagement (MaxDrawdown portfolio 5%, per-security 3%)
3. PortfolioConstruction (RiskParityPortfolioConstructionModel — HRP)
4. Execution (VolumeWeightedAveragePriceExecutionModel)

Fee model MUST load rates from `config/fee_schedules.json` by trade date.
STT changed October 1, 2024. Using hardcoded rates produces wrong backtest P&L.

Symbol mapper MUST pass round-trip test:
Dhan security_id → LEAN Symbol → Dhan security_id returns same ID.
Options expiry dates: ALWAYS from instrument master. NEVER calculated from calendar.
