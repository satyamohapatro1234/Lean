# Nexus MTF Confluence Strategy — Pre-Code Analysis
# =====================================================
# Written before main.py as a design spec.

# ─────────────────────────────────────────────────────────────────────
# SOURCE 1: Spider MTF Wave System v5.0
# ─────────────────────────────────────────────────────────────────────
# What it contributes:
#   - 4-level wave hierarchy (Quarterly → Monthly → Weekly → 6H)
#   - Grandmother score 0-4 (macro bias gating)
#   - Mother trend: higher close + higher low + expanding range
#   - Macro/Son state machine: Breakout / Supply / Bottom / Overshot
#   - 5 Trap Elimination Rules (2-candle, retest, vol sequence, close pos, time)
#   - Risk-based position sizing: risk_capital / stop_distance
#   - Chandelier trailing stop
#   - Fibonacci targets (1.272 partial, 1.618 full)
# Key numbers: monthly H/L are the PRIMARY structural levels
# Already converted → strategies/spider_wave/main.py

# ─────────────────────────────────────────────────────────────────────
# SOURCE 2: Buyside & Sellside Liquidity
# ─────────────────────────────────────────────────────────────────────
# What it contributes:
#   - ZigZag via ta.pivothigh/pivotlow (liqLen=7 bars each side)
#   - Clusters of pivot highs within ATR/liqMar → BUYSIDE LIQUIDITY zone
#   - Clusters of pivot lows within ATR/liqMar → SELLSIDE LIQUIDITY zone
#   - Cluster requires count > 2 (3+ pivots near same level)
#   - Breach detection: price tags the zone → starts "breach zone" extension
#   - Liquidity Void: gap between bar.l and bar.h[2] > ATR200 → unfilled space
#   - Void persists until a bar trades through it (mid-void crossover check)
#
# Key insight for strategy:
#   SELLSIDE LIQUIDITY = where sell stops cluster = price magnet BELOW
#   BUYSIDE LIQUIDITY  = where buy stops cluster  = price magnet ABOVE
#   Strategy: buy AFTER price sweeps SSL (stop hunt), then recovers above
#   Strategy: sell partial AT BSL (take profit at where stops get run)
#   Liquidity voids = price moves FAST through them = targets / gap fills

# ─────────────────────────────────────────────────────────────────────
# SOURCE 3: GTF Supply & Demand / Liquidity
# ─────────────────────────────────────────────────────────────────────
# What it contributes:
#   - EMA 20 / 50 / 200 (configurable)
#   - Supply zones: at swing highs → box from (high - ATR×box_width/10) to high
#   - Demand zones: at swing lows  → box from low to (low + ATR×box_width/10)
#   - Overlap filter: don't draw zone if another zone within 2×ATR
#   - BOS conversion: when price CLOSES above supply zone top → zone converts to BOS line
#   - BOS conversion: when price CLOSES below demand zone bottom → converts to BOS line
#   - f_sd_to_bos → mid-point becomes horizontal line extending right
#   - swing_length = 10 bars each side (ta.pivothigh/pivotlow)
#
# Key insight for strategy:
#   DEMAND ZONE = discounted price, potential institutional buy area
#   SUPPLY ZONE = premium price, potential institutional sell area
#   BOS line (converted zone) = strong support/resistance, previous S/D
#   EMA stack (price > EMA20 > EMA50 > EMA200) = strongest bullish alignment
#   Entry: price pulls back INTO demand zone while EMA stack bullish

# ─────────────────────────────────────────────────────────────────────
# SOURCE 4: Price Action Concepts (LuxAlgo v1.2.2)
# ─────────────────────────────────────────────────────────────────────
# What it contributes:
#   - Internal structure (iLen=5 bars pivot): smaller BOS/CHoCH 
#   - Swing structure (sLen=50 bars pivot): larger BOS/CHoCH
#   - BOS: close crosses above/below previous swing high/low (trend continuation)
#   - CHoCH: BOS in OPPOSITE direction of current trend (reversal warning)
#   - CHoCH+: CHoCH with higher low (bullish) or lower high (bearish) = stronger reversal
#   - Volumetric Order Blocks:
#       Bull OB: last bearish candle before a bullish BOS (institutional buy)
#       Bear OB: last bullish candle before a bearish BOS (institutional sell)
#       Mitigation: OB removed when price closes through middle or bottom
#       Volume-weighted: tracks buy/sell volume proportion inside OB
#   - Fair Value Gap (FVG): bar[2].high < bar[0].low (bullish gap = imbalance)
#                            bar[2].low > bar[0].high (bearish gap)
#   - Accumulation zone: 4-6 zigzag points forming higher lows + lower highs (range)
#   - Distribution zone: opposite of accumulation
#   - EQH/EQL: two pivot highs/lows within 0.1×ATR200 of each other = equal levels
#   - MTF scanner: 15m/1H/4H/1D internal trend direction
#
# Key insight for strategy:
#   BULLISH CHoCH = first sign of reversal (trend shifting from down to up)
#   BULLISH BOS   = confirmation of uptrend continuation
#   Order Block = institutional footprint, excellent support after BOS
#   FVG = price imbalance, will often get filled = short-term target/magnet
#   EQH = two equal highs = DOUBLE TOP liquidity above = BSL target
#   EQL = two equal lows  = DOUBLE BOTTOM SSL pool = entry trigger

# ─────────────────────────────────────────────────────────────────────
# COMBINED STRATEGY: Nexus MTF Confluence
# ─────────────────────────────────────────────────────────────────────

# NAME: Nexus MTF Confluence Strategy
# PHILOSOPHY: "Hunt stops, ride structure, respect levels"
#
# Core logic:
#   1. Macro context (Grandmother/Mother from Spider) = trade direction allowed
#   2. Structural alignment (BOS/CHoCH from PAC) = trend in gear
#   3. Liquidity sweep (Sellside hit from Liq indicator) = weak hands flushed
#   4. Zone support (Demand zone from GTF / Order Block from PAC) = institutional buy area
#   5. Oscillator confirmation (Williams %R bounce + VWAP reclaim) = momentum turning
#   6. Ichimoku filter (daily cloud) = medium-term trend gate
#   7. Trigger candle (Rule 4 + two-candle from Spider) = clean entry

# TIMEFRAME USAGE:
#   WEEKLY    → Ichimoku cloud (is price above/below kumo), Spider Grandmother
#   DAILY     → BOS/CHoCH direction, EMA stack, Demand zones, Order Blocks, FVG
#   DAILY     → Williams %R (14-period), VWAP (daily reset)
#   DAILY/6H  → Liquidity sweep detection, two-candle confirmation
#   6H        → Trigger candle quality (Rule 4), volume sequence (Rule 3)

# SCORING SYSTEM (max 10 points, need >= 6 for entry):
#
# MACRO LAYER (max 3 points):
#   [2pts] Grandmother score >= 3 (Bull)
#   [1pt]  Grandmother score == 2 (Weak)
#   [1pt]  Mother Wave valid (trend + range)
#
# TREND LAYER (max 3 points):
#   [2pts] Ichimoku: price above cloud AND Tenkan > Kijun (full bull)
#   [1pt]  Ichimoku: price above cloud only (partial bull)
#   [1pt]  Daily BOS confirmed (close above previous swing high)
#   Note: CHoCH gives +0.5pt bonus but requires it happened recently (< 10 bars)
#
# STRUCTURE / ZONE LAYER (max 2 points):
#   [1pt]  Price in or just above DEMAND ZONE (GTF) or BULLISH ORDER BLOCK (PAC)
#   [1pt]  EMA stack: price > EMA20 > EMA50 > EMA200 (fully aligned)
#          or price above EMA200 + EMA20 cross above EMA50 (partial = 0.5pt)
#
# MOMENTUM LAYER (max 2 points):
#   [1pt]  Williams %R: was below -80 (oversold) within last 5 bars, now > -50 (bounce)
#          OR VWAP: price just reclaimed VWAP from below (cross above)
#   [1pt]  Sellside Liquidity SWEPT: price tagged SSL zone within last 3 bars,
#          then closed back above SSL (stop hunt complete)
#
# TRIGGER LAYER (max 1 point):
#   [1pt]  Rule 4: close in top 30% of range, clean wick
#          + Rule 1: two consecutive 6H bars above the entry level
#          + Rule 3: volume surge on the setup candle
#
# BONUS (can push score above 10, but cap at 10):
#   [+1]  FVG below price pointing upward (unfilled gap = strong support)
#   [+1]  Equal Lows (EQL) swept → accumulation of stops triggered
#   [+1]  CHoCH+ detected recently (< 10 bars) → higher quality reversal

# ENTRY TYPES (matching Spider Wave's A/B/C/D framework):
#   A-PLUS:  Score >= 8 + Macro Breakout + Liq Sweep + OB support = FULL SIZE (1.0×)
#   A:       Score >= 6 + Macro Breakout                           = FULL SIZE (1.0×)
#   B-PLUS:  Score >= 7 + Overshot zone + Liq Sweep                = FULL SIZE (1.0×)
#   B:       Score >= 6 + Demand Zone bounce                       = HALF SIZE (0.5×)
#   C:       Score >= 6 + Son Breakout (weekly) in Supply zone     = HALF SIZE (0.5×)
#   D:       Score >= 5 + Son Bottom with FVG support              = QUARTER SIZE (0.25×)

# STOP LOSS (hierarchical, tightest wins):
#   Level 1: Below Order Block bottom (if in OB)
#   Level 2: Below Demand Zone bottom - 0.3×ATR buffer
#   Level 3: Below recent swing low (from PAC EQL or pivot low)
#   Level 4: Below entry - 1.5×ATR (absolute floor)
#   Final: Take the HIGHEST of these (tightest stop = best RR)

# TARGETS:
#   T1 (exit 30% of position): Nearest supply zone OR EMA resistance (minimum 1.5:1 RR)
#   T2 (exit 30% of position): Buyside liquidity zone OR EQH level (minimum 3:1 RR)
#   T3 (trail remaining 40%): Chandelier stop ATR × 2.5 (let runners run)
#   Hard exit: Fib 1.618 extension of monthly range (same as Spider Wave)

# RR FILTER: If T1 does not give at least 1.5:1 RR, SKIP the trade.
# This is critical for NSE swing trades with brokerage + slippage.
