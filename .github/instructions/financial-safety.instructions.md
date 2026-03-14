---
applyTo: "**"
---

# Financial Safety Instructions (Applies to All Files)

These rules apply to every file in the repository:

1. No API keys, access tokens, or passwords in any source file
2. All financial calculations must use date-aware lookups (not hardcoded values)
3. Lot sizes: Query `lot_size_history` table with trade date
4. Fee rates: Load from `config/fee_schedules.json` with trade date
5. Any order placement requires: pre-margin check + human confirmation step
6. LEAN price format: `int(raw_price * 10000)` — this is not negotiable
7. NSE option expiry dates: always from instrument master, never calculated
8. After Nov 2024: only Nifty50 (NSE) and Sensex (BSE) have weekly expiries
