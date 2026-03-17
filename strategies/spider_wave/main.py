"""
Spider MTF Wave System v5.0 — LEAN Python / QuantConnect
==========================================================
Converted from Pine Script v6 (Spider_MTF_v5.0) by Satya.

All 5 Trap Elimination Rules preserved:
  Rule 1: Two-candle close confirmation
  Rule 2: Retest and hold verification
  Rule 3: 3-candle volume sequence (build → surge → sustain)
  Rule 4: Close position ≥ top 30% of candle range
  Rule 5: NSE time-of-day filter

Wave hierarchy:
  Grandmother  → Quarterly (4 conditions scored 0–4)
  Mother       → Monthly   (trend + range validity)
  Macro Wave   → Price vs Monthly High/Low
  Son Wave     → Price vs 4-Week High/Low
  Trigger      → 6H candle confirmation

Important implementation notes:
  - For NSE, 1 trading day ≈ 1 six-hour bar (9:15–15:30 = 6h15m)
    So "two 6H candles" = two consecutive trading day closes above level.
  - Python 3.11 required  (.venv311 — pythonnet 2.0.53 constraint).
  - Brokerage: ZerodhaBrokerageModel; swap to DhanBrokerageModel when built.
  - Data: minute resolution from platform/data-pipeline/ (QuestDB → LEAN zip).
  - The NSE time-of-day filter (Rule 5) is applied to the completed 6H bar's
    time; since bars span the full session it is always True in this context.
    The filter is left in for forward-test / live compatibility.

Files:
  strategies/spider_wave/main.py   ← this file
  strategies/spider_wave/config.json ← lean-config.json override (optional)

Usage:
  python engine-wrapper/run_backtest.py --strategy SpiderWaveAlgorithm
"""

from AlgorithmImports import *
from collections import deque, namedtuple
import math

# ---------------------------------------------------------------------------
# Lightweight bar data structure (mirrors Pine Script bar variables)
# ---------------------------------------------------------------------------
Bar = namedtuple("Bar", ["open", "high", "low", "close", "volume", "time"])


def _make_bar(acc: dict) -> Bar:
    """Build a completed Bar from an accumulator dict."""
    return Bar(
        open=acc["open"],  high=acc["high"], low=acc["low"],
        close=acc["close"], volume=acc["vol"], time=acc.get("time")
    )


# ---------------------------------------------------------------------------
# Main Algorithm
# ---------------------------------------------------------------------------
class SpiderWaveAlgorithm(QCAlgorithm):
    """
    Spider MTF Wave System v5.0
    Faithful conversion of Pine Script v6 → QuantConnect LEAN Python.
    """

    # ═══════════════════════════════════════════════════════════════════════
    # INITIALIZE
    # ═══════════════════════════════════════════════════════════════════════
    def initialize(self):
        # ── Backtest period ─────────────────────────────────────────────
        self.set_start_date(2019, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(100_000)

        # ── Symbol ─────────────────────────────────────────────────────
        # Change via lean-config.json parameter: "symbol": "SBIN"
        ticker = self.get_parameter("symbol") or "SBIN"
        self._sym = self.add_equity(ticker, Resolution.MINUTE, Market.INDIA).symbol

        # ── Brokerage & fee model ───────────────────────────────────────
        self.set_brokerage_model(BrokerageName.ZERODHA_BROKERAGE, AccountType.MARGIN)
        # TODO: replace with DhanFeeModel when platform/strategies/spider-wave/fee_model.py built

        # ═══════════════════════════════════════════════════════════════
        # SECTION 0 ▸ PARAMETERS  (Pine Script: grp0 / grp1 / grp2)
        # ═══════════════════════════════════════════════════════════════
        # Risk Management
        self.p_risk_pct        = float(self.get_parameter("risk_pct")        or "1.0")
        self.p_atr_len         = int(self.get_parameter("atr_len")           or "14")
        self.p_atr_mult_norm   = float(self.get_parameter("atr_mult_norm")   or "1.5")
        self.p_atr_mult_high   = float(self.get_parameter("atr_mult_high")   or "2.5")
        self.p_atr_mult_trail  = float(self.get_parameter("atr_mult_trail")  or "2.0")

        # Trap Elimination Rules
        self.p_use_two_candle  = True    # Rule 1
        self.p_use_retest      = True    # Rule 2
        self.p_retest_atr_mult = 0.5     # Rule 2 — max depth in ATR multiples
        self.p_vol_len         = 20      # Rule 3 — volume MA length
        self.p_vol_surge_min   = 1.2     # Rule 3 — min surge multiplier
        self.p_vol_sustain_min = 0.6     # Rule 3 — min sustain (Bar0 vs Bar1)
        self.p_close_pos_pct   = 0.70    # Rule 4 — top 30% close (0.70 = 70th pct)
        self.p_wick_thresh     = 0.30    # Rule 4 — max upper wick ratio
        self.p_use_time_filter = True    # Rule 5 — avoid last 30 min of NSE session
        self.p_min_range_ratio = 0.70    # Mother — monthly range vs 6M average

        # ═══════════════════════════════════════════════════════════════
        # SECTION 1 ▸ HTF BAR ROLLING WINDOWS
        # Naming: _XY_bars where X=timeframe, oldest[last] newest[0]
        # appendleft() keeps [0] = most recent completed bar (Pine: p1)
        # Pine: close_6h[1] = our [0]; close_6h[2] = our [1]; etc.
        # ═══════════════════════════════════════════════════════════════
        self._6h_bars   = deque(maxlen=5)   # [0]=p1 [1]=p2 [2]=p3
        self._daily     = deque(maxlen=200) # for ATR rolling
        self._weekly    = deque(maxlen=6)   # [0]=p1 … [3]=p4 (4-week high/low)
        self._monthly   = deque(maxlen=8)   # [0]=p1 … [5]=p6
        self._quarterly = deque(maxlen=4)   # [0]=p1 [1]=p2

        # Volume history for 6H MA
        self._vol_6h_hist = deque(maxlen=25)

        # ── In-progress bar accumulators (None until first bar of period) ──
        self._acc_6h   = None
        self._acc_day  = None
        self._acc_week = None
        self._acc_mon  = None
        self._acc_qtr  = None

        # ── Daily ATR (rolling EMA-style — matches Pine ta.atr) ────────
        self._prev_day_close  = None
        self._tr_window       = deque(maxlen=20)   # true ranges
        self._atr_daily       = None               # current ATR value
        self._atr_daily_hist  = deque(maxlen=130)  # history for 6M SMA
        self._atr_6m_avg      = None               # 126-day SMA of ATR

        # ═══════════════════════════════════════════════════════════════
        # SECTION 11 ▸ RULE 2 — RETEST STATE (persistent across bars)
        # ═══════════════════════════════════════════════════════════════
        self._breakout_occurred = False
        self._retest_seen       = False

        # ═══════════════════════════════════════════════════════════════
        # SECTION 17–18 ▸ TRADE STATE
        # ═══════════════════════════════════════════════════════════════
        self._bars_since_entry = 0
        self._entry_stop       = None   # hard stop price
        self._trail_high       = None   # highest high since entry
        self._partial_done     = False  # Fib 1.272 partial exit fired?
        self._entry_type       = None   # "A" | "B" | "C" | "D"

        # ── 6H bar ID tracking (new bar = new day for NSE) ─────────────
        self._last_6h_day = None

        # ── Warm-up: 13 calendar months for 6 completed monthly bars ───
        self.set_warm_up(TimeSpan.from_days(400))

        self.log(f"Spider MTF Wave System v5.0 — {ticker} initialized")

    # ═══════════════════════════════════════════════════════════════════════
    # ON DATA  (called every minute bar)
    # ═══════════════════════════════════════════════════════════════════════
    def on_data(self, data: Slice):
        if not data.bars.contains_key(self._sym):
            return

        bar = data.bars[self._sym]
        t   = bar.end_time  # minute bar end time

        # Update ALL timeframe accumulators with this minute bar
        self._update_bars(bar, t)

        # Fire strategy logic when a 6H bar just completed (new trading day)
        day_id = t.date()
        if self._last_6h_day is None:
            self._last_6h_day = day_id
            return

        if day_id != self._last_6h_day:
            self._last_6h_day = day_id
            if not self.is_warming_up:
                self._evaluate_signals(t)

    # ═══════════════════════════════════════════════════════════════════════
    # _update_bars — accumulate minute bars into all HTF timeframes
    # ═══════════════════════════════════════════════════════════════════════
    def _update_bars(self, bar, t):
        o, h, l, c, v = bar.open, bar.high, bar.low, bar.close, bar.volume

        def _acc_update(acc, high, low, close, vol):
            acc["high"]  = max(acc["high"], high)
            acc["low"]   = min(acc["low"],  low)
            acc["close"] = close
            acc["vol"]  += vol

        # ── DAILY ──────────────────────────────────────────────────────
        day_id = t.date()
        if self._acc_day is None or self._acc_day["id"] != day_id:
            if self._acc_day is not None:
                self._on_daily_completed(_make_bar(self._acc_day))
            self._acc_day = {"id": day_id, "open": o, "high": h,
                             "low": l, "close": c, "vol": v, "time": t}
        else:
            _acc_update(self._acc_day, h, l, c, v)

        # ── SIX-HOUR (NSE ≈ 1 per trading day: 9:15–15:30) ─────────────
        # Same ID as daily — each trading day = one 6H bar for NSE
        if self._acc_6h is None or self._acc_6h["id"] != day_id:
            if self._acc_6h is not None:
                completed = _make_bar(self._acc_6h)
                self._6h_bars.appendleft(completed)
                self._vol_6h_hist.appendleft(completed.volume)
            self._acc_6h = {"id": day_id, "open": o, "high": h,
                            "low": l, "close": c, "vol": v, "time": t}
        else:
            _acc_update(self._acc_6h, h, l, c, v)

        # ── WEEKLY (ISO week: Mon–Fri) ──────────────────────────────────
        iso = t.isocalendar()
        week_id = (iso[0], iso[1])
        if self._acc_week is None or self._acc_week["id"] != week_id:
            if self._acc_week is not None:
                self._weekly.appendleft(_make_bar(self._acc_week))
            self._acc_week = {"id": week_id, "open": o, "high": h,
                              "low": l, "close": c, "vol": v, "time": t}
        else:
            _acc_update(self._acc_week, h, l, c, v)

        # ── MONTHLY ────────────────────────────────────────────────────
        month_id = (t.year, t.month)
        if self._acc_mon is None or self._acc_mon["id"] != month_id:
            if self._acc_mon is not None:
                self._monthly.appendleft(_make_bar(self._acc_mon))
            self._acc_mon = {"id": month_id, "open": o, "high": h,
                             "low": l, "close": c, "vol": v, "time": t}
        else:
            _acc_update(self._acc_mon, h, l, c, v)

        # ── QUARTERLY ──────────────────────────────────────────────────
        qtr_id = (t.year, (t.month - 1) // 3)
        if self._acc_qtr is None or self._acc_qtr["id"] != qtr_id:
            if self._acc_qtr is not None:
                self._quarterly.appendleft(_make_bar(self._acc_qtr))
            self._acc_qtr = {"id": qtr_id, "open": o, "high": h,
                             "low": l, "close": c, "vol": v, "time": t}
        else:
            _acc_update(self._acc_qtr, h, l, c, v)

    def _on_daily_completed(self, bar: Bar):
        """Compute ATR when a daily bar closes — Pine: ta.atr(atrLen) on D."""
        if self._prev_day_close is None:
            self._prev_day_close = bar.close
            return
        tr = max(
            bar.high - bar.low,
            abs(bar.high - self._prev_day_close),
            abs(bar.low  - self._prev_day_close)
        )
        self._tr_window.append(tr)
        if len(self._tr_window) >= self.p_atr_len:
            self._atr_daily = sum(list(self._tr_window)[-self.p_atr_len:]) / self.p_atr_len
            self._atr_daily_hist.append(self._atr_daily)
            if len(self._atr_daily_hist) >= 126:
                self._atr_6m_avg = (sum(list(self._atr_daily_hist)[-126:]) / 126)
        self._prev_day_close = bar.close

    # ═══════════════════════════════════════════════════════════════════════
    # _evaluate_signals — main signal engine (fires on each completed 6H bar)
    # ═══════════════════════════════════════════════════════════════════════
    def _evaluate_signals(self, t):

        # ── Guard: require minimum history ─────────────────────────────
        if (len(self._6h_bars)   < 3 or
            len(self._monthly)   < 6 or
            len(self._weekly)    < 4 or
            len(self._quarterly) < 2 or
            self._atr_daily is None):
            return

        atr = self._atr_daily   # shorthand

        # ═══════════════════════════════════════════════════════════════
        # SECTION 2 ▸ GRANDMOTHER WAVE (Quarterly)
        # Pine: qtrScore = sum of 4 conditions; 3–4 = Bull; 2 = Weak
        # ═══════════════════════════════════════════════════════════════
        qp1 = self._quarterly[0]    # last completed quarter (Pine: p1)
        qp2 = self._quarterly[1]    # two quarters ago       (Pine: p2)
        qtr_cur = self._acc_qtr     # in-progress current quarter

        qtr_range_p1     = qp1.high - qp1.low
        qtr_close_pos_p1 = ((qp1.close - qp1.low) / qtr_range_p1
                            if qtr_range_p1 > 0 else 0.5)

        qtr_A = qtr_cur["open"]  > qp1.close         # gap-up open
        qtr_B = qp1.low          > qp2.low            # higher low
        qtr_C = qtr_close_pos_p1 >= 0.60              # strong close position
        qtr_D = qtr_cur["close"] > qp1.high           # breaking above prev quarter

        qtr_score      = sum([qtr_A, qtr_B, qtr_C, qtr_D])
        is_gma_bull    = qtr_score >= 3
        is_gma_weak    = qtr_score == 2
        qtr_size_mult  = (1.0 if is_gma_bull else
                          0.5 if is_gma_weak  else 0.0)

        # ═══════════════════════════════════════════════════════════════
        # SECTION 3 ▸ MOTHER WAVE (Monthly)
        # Pine: motherCond_A/B/C + isInsideMonth + isRangeValid
        # ═══════════════════════════════════════════════════════════════
        mp = [self._monthly[i] for i in range(6)]   # mp[0]=p1 … mp[5]=p6

        mother_A = mp[0].close > mp[1].close
        mother_B = mp[0].low   >= (mp[1].low - 0.5 * atr)
        mother_C = (mp[0].high - mp[0].low) >= (mp[2].high - mp[2].low)
        is_mother_trend = mother_A and mother_B and mother_C

        ranges     = [(mp[i].high - mp[i].low) for i in range(6)]
        avg_range  = sum(ranges) / 6
        is_inside  = (mp[0].high <= mp[1].high) and (mp[0].low >= mp[1].low)
        is_range_valid = (ranges[0] >= 1.5 * atr and
                          ranges[0] >= self.p_min_range_ratio * avg_range and
                          not is_inside)

        monthly_high = mp[0].high   # Pine: monthlyHigh = mthHigh_p1
        monthly_low  = mp[0].low    # Pine: monthlyLow  = mthLow_p1

        # ═══════════════════════════════════════════════════════════════
        # SECTION 4 ▸ MACRO + SON WAVE STATE MACHINES
        # Pine: isMacroBreakout / isMacroSupply / isMacroBottom / isMacroOvershot
        # ═══════════════════════════════════════════════════════════════

        # Use last completed 6H bar's close as "current price" (Pine: close)
        close = self._6h_bars[0].close

        is_macro_breakout = close > monthly_high
        is_macro_supply   = monthly_low <= close <= monthly_high
        is_macro_bottom   = (monthly_low - atr) <= close < monthly_low
        is_macro_overshot = close < (monthly_low - atr)

        # 4-week high/low (Pine: weeklyHigh = max of wkHigh_p1..wkHigh_p4)
        wp = [self._weekly[i] for i in range(4)]
        weekly_high = max(w.high for w in wp)
        weekly_low  = min(w.low  for w in wp)

        # ═══════════════════════════════════════════════════════════════
        # SECTION 5 ▸ VOLATILITY REGIME
        # Pine: isHighVol = atrDaily > atrAvg6m * 1.3
        # ═══════════════════════════════════════════════════════════════
        is_high_vol = (self._atr_6m_avg is not None and
                       atr > self._atr_6m_avg * 1.3)
        atr_mult_sl = self.p_atr_mult_high if is_high_vol else self.p_atr_mult_norm

        # ═══════════════════════════════════════════════════════════════
        # SECTION 6 ▸ 6H CANDLE — BASE METRICS
        # Pine: _6h = current bar; _6h_1 = [1]; _6h_2 = [2]
        # Our mapping: _6h_bars[0]=Pine "close_6h", [1]=Pine "close_6h_1", etc.
        # ═══════════════════════════════════════════════════════════════
        b0  = self._6h_bars[0]   # Pine: current bar (just closed)
        b1  = self._6h_bars[1]   # Pine: close_6h_1
        b2  = self._6h_bars[2]   # Pine: close_6h_2

        open_6h    = b0.open;   close_6h  = b0.close
        high_6h    = b0.high;   low_6h    = b0.low
        vol_6h     = b0.volume

        range_6h       = high_6h - low_6h
        upper_wick_6h  = high_6h - max(close_6h, open_6h)
        body_6h        = abs(close_6h - open_6h)

        open_6h_1  = b1.open;   close_6h_1 = b1.close
        high_6h_1  = b1.high;   low_6h_1   = b1.low
        vol_6h_1   = b1.volume
        range_6h_1 = high_6h_1 - low_6h_1

        vol_6h_2   = b2.volume

        # Volume moving average (Pine: ta.sma(vol_6h, volLen))
        vol_hist = list(self._vol_6h_hist)
        vol_ma   = (sum(vol_hist[:self.p_vol_len]) / self.p_vol_len
                   if len(vol_hist) >= self.p_vol_len else None)

        # ═══════════════════════════════════════════════════════════════
        # SECTION 7 ▸ RULE 4 — CLOSE POSITION FILTER
        # "Close must be in top 30% of candle range + clean upper wick"
        # Pine: closePosition = (close - low) / (high - low) >= 0.70
        # ═══════════════════════════════════════════════════════════════
        close_pos_0 = ((close_6h  - low_6h)   / range_6h   if range_6h   > 0 else 0.5)
        close_pos_1 = ((close_6h_1 - low_6h_1) / range_6h_1 if range_6h_1 > 0 else 0.5)

        rule4_cur  = (close_pos_0 >= self.p_close_pos_pct and
                      (upper_wick_6h / max(range_6h, 0.001)) < self.p_wick_thresh and
                      close_6h > open_6h)
        rule4_prev = (close_pos_1 >= self.p_close_pos_pct and close_6h_1 > open_6h_1)

        # ═══════════════════════════════════════════════════════════════
        # SECTION 8 ▸ RULE 3 — 3-CANDLE VOLUME SEQUENCE
        # Pine:
        #   rule3_buildUp  = vol_6h_2 <= vol_6h_1          (built into breakout)
        #   rule3_surge    = vol_6h_1 >= volMA × surgeMin  (breakout bar surged)
        #   rule3_sustain  = vol_6h   >= vol_6h_1 × susMin (current bar sustains)
        # ═══════════════════════════════════════════════════════════════
        if vol_ma and vol_ma > 0:
            rule3_build   = vol_6h_2 <= vol_6h_1
            rule3_surge   = vol_6h_1 >= vol_ma * self.p_vol_surge_min
            rule3_sustain = vol_6h   >= vol_6h_1 * self.p_vol_sustain_min
        else:
            rule3_build = rule3_surge = rule3_sustain = False

        rule3_vol_seq = rule3_build and rule3_surge and rule3_sustain  # used in confirm_A

        # ═══════════════════════════════════════════════════════════════
        # SECTION 9 ▸ RULE 5 — NSE TIME-OF-DAY FILTER
        # Pine: isLastHalfHour = (hour == 9 and minute >= 30) or hour > 9 [UTC]
        # Note: For NSE 6H bars spanning 9:15–15:30, signals fire at day-start.
        # The filter is preserved for forward-test / live compatibility.
        # In backtesting on daily 6H bars it evaluates against the bar's close time.
        # ═══════════════════════════════════════════════════════════════
        if self.p_use_time_filter:
            # t is the minute bar time at signal evaluation (start of new day ≈ 9:15 IST)
            # bar's close time (b0.time) = end of previous trading day ≈ 15:30 IST
            bar_end = b0.time
            if bar_end is not None:
                h_ist = bar_end.hour    # LEAN uses exchange timezone (IST for NSE)
                m_ist = bar_end.minute
                # Last 30 min = 15:00–15:30 IST
                is_last_30 = (h_ist == 15 and m_ist >= 0) or h_ist > 15
                rule5_ok   = not is_last_30
            else:
                rule5_ok = True
        else:
            rule5_ok = True

        # ═══════════════════════════════════════════════════════════════
        # SECTION 10 ▸ RULE 1 — TWO-CANDLE CLOSE CONFIRMATION
        # Pine: close_6h_1 > level AND close_6h > level AND close_6h >= close_6h_1
        # ═══════════════════════════════════════════════════════════════
        if self.p_use_two_candle:
            rule1_macro = (close_6h_1 > monthly_high and
                           close_6h   > monthly_high and
                           close_6h   >= close_6h_1)
            rule1_overshoot_rev = (close_6h_1 > monthly_low and
                                   close_6h   > monthly_low and
                                   close_6h   >= close_6h_1)
            rule1_son_break = (close_6h_1 > weekly_high and
                               close_6h   > weekly_high and
                               close_6h   >= close_6h_1)
            rule1_son_bot   = (close_6h_1 > weekly_low  and
                               close_6h   > weekly_low  and
                               close_6h   >= close_6h_1)
        else:
            rule1_macro         = close_6h > monthly_high
            rule1_overshoot_rev = close_6h > monthly_low
            rule1_son_break     = close_6h > weekly_high
            rule1_son_bot       = close_6h > weekly_low

        # ═══════════════════════════════════════════════════════════════
        # SECTION 11 ▸ RULE 2 — RETEST AND HOLD  (stateful)
        # Pine: breakoutOccurred_M, retestSeen_M — var bool persisted
        # ═══════════════════════════════════════════════════════════════

        # Breakout occurred: first close above monthly high
        if close_6h_1 > monthly_high and not self._breakout_occurred:
            self._breakout_occurred = True

        # Retest: price pulled back to within retestATRMult × ATR of the level
        if self._breakout_occurred and not self._retest_seen:
            if (low_6h_1  <= monthly_high + self.p_retest_atr_mult * atr and
                high_6h_1 >= monthly_high):
                self._retest_seen = True

        # Reset: price fell well below (breakout fully failed)
        if close_6h < monthly_high - 1.5 * atr:
            self._breakout_occurred = False
            self._retest_seen       = False

        if self.p_use_retest:
            rule2_macro = (self._breakout_occurred and
                           self._retest_seen and
                           close_6h > monthly_high and
                           close_6h > open_6h)
        else:
            rule2_macro = True

        # ═══════════════════════════════════════════════════════════════
        # SECTION 12 ▸ COMBINED CONFIRMATION ENGINE
        # Pine: baseCandle = rule4_current and rule5_timeOk
        # confirmA uses rule3_volSeq (full sequence)
        # confirmB/C/D use rule3_surge only (Pine matches)
        # ═══════════════════════════════════════════════════════════════
        base_candle = rule4_cur and rule5_ok

        confirm_A = (rule1_macro and rule2_macro and
                     rule3_vol_seq and base_candle and
                     close_6h > weekly_high)

        confirm_B = (rule1_overshoot_rev and rule3_surge and
                     base_candle and close_6h > weekly_low)

        confirm_C = (rule1_son_break and rule3_surge and
                     base_candle and is_macro_supply)

        confirm_D = (rule1_son_bot and rule3_surge and
                     base_candle and (is_macro_supply or is_macro_bottom))

        # ═══════════════════════════════════════════════════════════════
        # SECTION 13 ▸ ENTRY SIGNALS
        # Pine: fullStack = baseFilter and (isGrandmotherBull or isGrandmotherWeak)
        # ═══════════════════════════════════════════════════════════════
        base_filter = is_mother_trend and is_range_valid
        full_stack  = base_filter and (is_gma_bull or is_gma_weak)

        entry_A = full_stack and is_macro_breakout and confirm_A
        entry_B = full_stack and is_macro_overshot and confirm_B
        entry_C = full_stack and is_macro_supply   and confirm_C
        entry_D = full_stack and (is_macro_supply or is_macro_bottom) and confirm_D

        long_signal = entry_A or entry_B or entry_C or entry_D

        # ═══════════════════════════════════════════════════════════════
        # SECTION 14 ▸ TRAP DETECTION — EARLY WARNING
        # Pine: volCollapse + isDojiAtLevel → trapWarning
        # ═══════════════════════════════════════════════════════════════
        in_trade = self.portfolio[self._sym].invested

        vol_collapse   = in_trade and vol_6h < vol_6h_1 * 0.7
        is_doji_at_lvl = (range_6h > 0 and
                          (body_6h / range_6h) < 0.3 and
                          abs(close_6h - monthly_high) < 0.3 * atr)
        trap_warning   = in_trade and vol_collapse and is_doji_at_lvl

        if trap_warning:
            self.log(f"⚠ TRAP WARNING | {self._sym} | {t.date()} | "
                     f"Price:{close_6h:.2f} | VolRatio:{vol_6h/vol_6h_1:.2f}")

        # ═══════════════════════════════════════════════════════════════
        # SECTION 15 ▸ STOP DISTANCE + POSITION SIZING
        # Pine: riskRupees = equity × riskPct% × qtrSizeMult
        #       riskBasedQty = floor(riskRupees / stopDist)
        # ═══════════════════════════════════════════════════════════════
        atr_stop_dist  = atr_mult_sl * atr
        stop_dist      = max(atr_stop_dist, atr * 0.5)   # floor: 0.5 ATR

        risk_capital   = (self.portfolio.total_portfolio_value *
                          (self.p_risk_pct / 100.0) *
                          qtr_size_mult)
        risk_based_qty = int(math.floor(risk_capital / stop_dist)) if stop_dist > 0 else 0

        # ═══════════════════════════════════════════════════════════════
        # SECTION 16 ▸ FIBONACCI TARGETS
        # Pine: fib1272 = monthlyHigh + monthRange × 0.272
        #       fib1618 = monthlyHigh + monthRange × 0.618
        # ═══════════════════════════════════════════════════════════════
        month_range = monthly_high - monthly_low
        fib1272     = monthly_high + month_range * 0.272
        fib1618     = monthly_high + month_range * 0.618

        # ═══════════════════════════════════════════════════════════════
        # SECTION 17 ▸ EXIT CONDITIONS
        # Pine: minHoldBars = 30 (6H bars ≈ 30 days for NSE)
        # ═══════════════════════════════════════════════════════════════
        min_hold = 30   # bars since entry before structure/trail exits fire

        # Update per-bar counters
        if in_trade:
            self._bars_since_entry += 1
            self._trail_high = max(self._trail_high or high_6h, high_6h)
        else:
            self._bars_since_entry = 0
            self._trail_high       = None

        since = self._bars_since_entry

        # Hard ATR stop (immediate — fires at any point after min hold)
        hard_stop = (in_trade and
                     self._entry_stop is not None and
                     since >= min_hold and
                     close_6h < self._entry_stop)

        # Structure break (monthly low fully broken)
        struct_break = (in_trade and since >= min_hold and close_6h < monthly_low)

        # Fibonacci partial exit — 50% at Fib 1.272
        partial_exit = (in_trade and
                        not self._partial_done and
                        high_6h >= fib1272 and
                        since >= min_hold)

        # Full exit at Fib 1.618
        full_exit = in_trade and high_6h >= fib1618

        # Chandelier trailing stop
        trail_stop = (None if self._trail_high is None
                      else self._trail_high - self.p_atr_mult_trail * atr)
        trail_exit = (in_trade and
                      trail_stop is not None and
                      since >= min_hold and
                      close_6h < trail_stop)

        exit_signal = hard_stop or full_exit or trail_exit or struct_break

        # ═══════════════════════════════════════════════════════════════
        # SECTION 18 ▸ STRATEGY EXECUTION
        # Order of operations: partial → full exit → entry
        # Pine: strategy.entry does not fire if position already open
        # ═══════════════════════════════════════════════════════════════
        current_qty = int(self.portfolio[self._sym].quantity)

        # ── PARTIAL EXIT at Fib 1.272 (50%) ───────────────────────────
        if partial_exit and current_qty > 0:
            half = max(1, current_qty // 2)
            self.market_order(self._sym, -half, tag="Partial50_Fib1272")
            self._partial_done = True
            self.log(f"PARTIAL EXIT | {self._sym} | {t.date()} | "
                     f"Sold:{half} | Fib1272:{fib1272:.2f}")

        # ── FULL EXIT ─────────────────────────────────────────────────
        if exit_signal and in_trade:
            reason = ("HardStop"   if hard_stop   else
                      "Fib1618"    if full_exit    else
                      "StructBreak" if struct_break else
                      "TrailStop")
            self.liquidate(self._sym, tag=f"Exit_{reason}")
            self._entry_stop       = None
            self._trail_high       = None
            self._partial_done     = False
            self._breakout_occurred = False   # reset Rule 2 after exit
            self._retest_seen       = False
            self.log(f"EXIT {reason} | {self._sym} | {t.date()} | "
                     f"Price:{close_6h:.2f} | Held:{since} bars")

        # ── ENTRY ─────────────────────────────────────────────────────
        # Guard: not in trade, grandmother not bear, qty > 0
        if (long_signal and
            not in_trade and
            not exit_signal and          # don't enter same bar we just exited
            qtr_size_mult > 0 and
            risk_based_qty > 0):

            lbl = "A" if entry_A else "B" if entry_B else "C" if entry_C else "D"
            self._entry_type = lbl

            # Set initial hard stop
            if entry_A:
                self._entry_stop = close_6h - atr_stop_dist
            elif entry_B:
                self._entry_stop = monthly_low - atr
            elif entry_C:
                self._entry_stop = weekly_low  - 0.5 * atr
            else:  # entry_D
                self._entry_stop = monthly_low - atr

            self.market_order(self._sym, risk_based_qty, tag=f"Entry_{lbl}")
            self._bars_since_entry  = 0
            self._partial_done      = False
            self._trail_high        = None

            # Reset Rule 2 state so next trade gets a fresh start
            self._breakout_occurred = False
            self._retest_seen       = False

            self.log(
                f"ENTRY {lbl} | {self._sym} | {t.date()} | "
                f"Qty:{risk_based_qty} | Price:{close_6h:.2f} | "
                f"Stop:{self._entry_stop:.2f} | "
                f"Fib1272:{fib1272:.2f} | Fib1618:{fib1618:.2f} | "
                f"ATR:{atr:.2f} | Vol:{'HIGH' if is_high_vol else 'NORMAL'} | "
                f"Gma:{qtr_score}/4 | QtrMult:{qtr_size_mult}"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # on_order_event — log all fills for the trade journal
    # ═══════════════════════════════════════════════════════════════════════
    def on_order_event(self, order_event: OrderEvent):
        if order_event.status == OrderStatus.FILLED:
            self.log(
                f"FILL | {order_event.symbol} | "
                f"Qty:{order_event.fill_quantity:+.0f} | "
                f"Price:{order_event.fill_price:.2f} | "
                f"Tag:{order_event.ticket.tag}"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # on_end_of_algorithm — print final summary
    # ═══════════════════════════════════════════════════════════════════════
    def on_end_of_algorithm(self):
        port = self.portfolio
        self.log("═" * 60)
        self.log("SPIDER MTF WAVE SYSTEM v5.0 — FINAL SUMMARY")
        self.log("═" * 60)
        self.log(f"  Symbol            : {self._sym}")
        self.log(f"  Starting Capital  : {self.starting_portfolio_value:,.2f}")
        self.log(f"  Final Value       : {port.total_portfolio_value:,.2f}")
        pnl = port.total_portfolio_value - self.starting_portfolio_value
        pct = pnl / self.starting_portfolio_value * 100
        self.log(f"  Net P&L           : {pnl:+,.2f} ({pct:+.2f}%)")
        self.log(f"  Total Trades      : {self.trade_builder.closed_trade_count}")
        self.log("═" * 60)
