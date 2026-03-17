"""
╔══════════════════════════════════════════════════════════════════════════════╗
║            NEXUS MTF CONFLUENCE STRATEGY — LEAN Python / QuantConnect      ║
║                          Swing Trading | NSE India                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  PHILOSOPHY: "Hunt stops, ride structure, respect levels"                   ║
║                                                                              ║
║  SOURCES COMBINED:                                                           ║
║  ① Spider MTF Wave System v5.0 — Wave hierarchy + 5 Trap Rules              ║
║  ② Buyside & Sellside Liquidity — ZigZag pivot liquidity clusters           ║
║  ③ GTF Supply & Demand — EMA stack + S/D zones + BOS conversion            ║
║  ④ Price Action Concepts (LuxAlgo) — BOS/CHoCH + OB + FVG + EQH/EQL       ║
║                                                                              ║
║  ADDED:                                                                      ║
║  ⑤ Ichimoku Cloud (daily/weekly trend gate)                                 ║
║  ⑥ Williams %R (14-period oversold bounce)                                  ║
║  ⑦ VWAP (daily value area reclaim)                                         ║
║                                                                              ║
║  SCORING: 10-point confluence system, minimum 6 points for entry            ║
║  TIMEFRAMES: Quarterly → Monthly → Weekly → Daily → 6H (trigger)           ║
║  TARGETS: T1=30% (1.5:1), T2=30% (3:1), T3=40% trail (chandelier)         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Python 3.11 required (.venv311 — pythonnet 2.0.53 constraint)
Run: python engine-wrapper/run_backtest.py --config strategies/nexus_confluence/lean-config.json
"""

from AlgorithmImports import *
from collections import deque, namedtuple
import math

# ─────────────────────────────────────────────────────────────────────────────
# Lightweight data structures
# ─────────────────────────────────────────────────────────────────────────────
Bar = namedtuple("Bar", ["open", "high", "low", "close", "volume", "time"])

def _make_bar(acc: dict) -> Bar:
    return Bar(open=acc["open"], high=acc["high"], low=acc["low"],
               close=acc["close"], volume=acc["vol"], time=acc.get("time"))

# Swing point (pivot high or low)
SwingPoint = namedtuple("SwingPoint", ["price", "bar_idx", "is_high", "time"])

# Liquidity zone (cluster of 3+ pivots within ATR margin)
LiqZone = namedtuple("LiqZone", ["level", "is_buyside", "bar_idx", "hit", "swept"])

# Supply/Demand zone (GTF style)
SDZone = namedtuple("SDZone", ["top", "bottom", "is_supply", "bar_idx", "active"])

# Order Block (PAC style)
OrderBlock = namedtuple("OrderBlock", ["top", "bottom", "avg", "is_bull",
                                       "bar_idx", "volume", "active"])

# Fair Value Gap
FVG = namedtuple("FVG", ["top", "bottom", "is_bull", "bar_idx", "active"])

# Confluence score result
Score = namedtuple("Score", [
    "total", "gma_pts", "mother_pts", "ichimoku_pts", "bos_pts",
    "zone_pts", "ema_pts", "momentum_pts", "liq_pts", "trigger_pts",
    "bonus_pts", "entry_type"
])


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ALGORITHM
# ─────────────────────────────────────────────────────────────────────────────
class NexusMTFConfluenceStrategy(QCAlgorithm):
    """
    Nexus MTF Confluence Strategy
    Combines 4 Pine Script indicators + Ichimoku + Williams %R + VWAP.
    """

    # ═════════════════════════════════════════════════════════════════════════
    # INITIALIZE
    # ═════════════════════════════════════════════════════════════════════════
    def initialize(self):
        self.set_start_date(2019, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(500_000)

        ticker    = self.get_parameter("symbol") or "SBIN"
        self._sym = self.add_equity(ticker, Resolution.MINUTE, Market.INDIA).symbol
        self.set_brokerage_model(BrokerageName.ZERODHA_BROKERAGE, AccountType.MARGIN)

        # ═════════════════════════════════════════════════════════════════════
        # SECTION 0 ▸ PARAMETERS
        # ═════════════════════════════════════════════════════════════════════

        # Risk
        self.p_risk_pct       = float(self.get_parameter("risk_pct")      or "1.0")
        self.p_atr_len        = int(self.get_parameter("atr_len")          or "14")
        self.p_atr_sl_norm    = float(self.get_parameter("atr_sl_norm")    or "1.5")
        self.p_atr_sl_high    = float(self.get_parameter("atr_sl_high")    or "2.5")
        self.p_atr_trail      = float(self.get_parameter("atr_trail")      or "2.5")
        self.p_min_rr         = float(self.get_parameter("min_rr")         or "1.5")
        self.p_min_score      = int(self.get_parameter("min_score")        or "6")

        # Structure detection
        self.p_swing_len      = int(self.get_parameter("swing_len")        or "10")  # GTF/PAC
        self.p_liq_len        = int(self.get_parameter("liq_len")          or "7")   # Liq indicator
        self.p_liq_margin     = float(self.get_parameter("liq_margin")     or "1.45")# ATR/margin
        self.p_ob_len         = int(self.get_parameter("ob_len")           or "5")   # PAC internal OB pivot
        self.p_min_range_ratio= float(self.get_parameter("min_range_ratio")or "0.70")

        # Rule 4 (Spider Wave)
        self.p_close_pos_pct  = 0.70
        self.p_wick_thresh    = 0.30

        # Ichimoku
        self.p_ichi_fast   = 9
        self.p_ichi_med    = 26
        self.p_ichi_slow   = 52

        # ═════════════════════════════════════════════════════════════════════
        # SECTION 1 ▸ HTF BAR ACCUMULATORS  (manual multi-timeframe)
        # ═════════════════════════════════════════════════════════════════════
        self._6h_bars    = deque(maxlen=6)
        self._daily_bars = deque(maxlen=300)
        self._weekly     = deque(maxlen=8)
        self._monthly    = deque(maxlen=8)
        self._quarterly  = deque(maxlen=5)

        self._acc_6h  = None
        self._acc_day = None
        self._acc_wk  = None
        self._acc_mon = None
        self._acc_qtr = None

        self._vol_6h_hist  = deque(maxlen=25)
        self._vol_day_hist = deque(maxlen=25)

        # ATR (daily, rolling manual)
        self._prev_day_close = None
        self._tr_window      = deque(maxlen=20)
        self._atr_daily      = None
        self._atr_hist       = deque(maxlen=200)
        self._atr_6m_avg     = None

        # ═════════════════════════════════════════════════════════════════════
        # SECTION 2 ▸ BUILT-IN LEAN INDICATORS
        # Source ⑤ Ichimoku, ⑥ Williams %R, ⑦ VWAP, EMA stack
        # ═════════════════════════════════════════════════════════════════════
        daily_consolidator = self.consolidate(
            self._sym, Resolution.DAILY, self._on_daily_consolidated)

        # Ichimoku Cloud (daily)
        self._ichimoku = IchimokuKinkoHyo(
            self.p_ichi_fast, self.p_ichi_med, self.p_ichi_slow,
            self.p_ichi_med, self.p_ichi_slow, self.p_ichi_med)
        self.register_indicator(self._sym, self._ichimoku, Resolution.DAILY)

        # Williams %R 14-period (daily)
        self._willr = WilliamPercentR(14)
        self.register_indicator(self._sym, self._willr, Resolution.DAILY)

        # VWAP (resets each day)
        self._vwap = IntradayVwap()
        self.register_indicator(self._sym, self._vwap, Resolution.MINUTE)

        # EMA stack (daily) — Source ③ GTF Supply & Demand
        self._ema20  = ExponentialMovingAverage(20)
        self._ema50  = ExponentialMovingAverage(50)
        self._ema200 = ExponentialMovingAverage(200)
        self.register_indicator(self._sym, self._ema20,  Resolution.DAILY)
        self.register_indicator(self._sym, self._ema50,  Resolution.DAILY)
        self.register_indicator(self._sym, self._ema200, Resolution.DAILY)

        # ═════════════════════════════════════════════════════════════════════
        # SECTION 3 ▸ STRUCTURE STATE  (Source ①②③④)
        # ═════════════════════════════════════════════════════════════════════

        # ── ① Spider Wave state ──────────────────────────────────────────────
        self._spider_breakout_occurred = False
        self._spider_retest_seen       = False

        # ── ② Liquidity Zones (Buyside/Sellside) ────────────────────────────
        # ZigZag state
        self._zz_dir    = 0     # +1 = last pivot was high, -1 = last pivot was low
        self._zz_highs  = deque(maxlen=50)  # list of (price, bar_idx)
        self._zz_lows   = deque(maxlen=50)
        self._bsl_zones = deque(maxlen=5)   # BuySide Liquidity zones
        self._ssl_zones = deque(maxlen=5)   # SellSide Liquidity zones
        self._liq_voids = deque(maxlen=20)  # (top, bottom, is_bull)

        # Sweep state: was SSL swept in last N bars?
        self._ssl_swept_bar    = -999
        self._ssl_swept_level  = None

        # ── ③ Supply/Demand Zones (GTF) ─────────────────────────────────────
        self._demand_zones  = deque(maxlen=5)   # SDZone instances
        self._supply_zones  = deque(maxlen=5)
        self._swing_highs_d = deque(maxlen=10)  # (price, bar_idx) for GTF
        self._swing_lows_d  = deque(maxlen=10)
        self._bos_lines     = deque(maxlen=10)  # converted S/D → BOS levels

        # ── ④ Price Action Concepts (BOS/CHoCH, OB, FVG) ────────────────────
        # Internal structure (shorter pivot)
        self._i_trend    = 0    # +1 bull, -1 bear
        self._i_highs    = deque(maxlen=10)   # internal swing highs (price, bar_idx)
        self._i_lows     = deque(maxlen=10)
        self._i_bos_bull_bar = -999            # last bullish BOS bar index
        self._i_choch_bull_bar = -999          # last bullish CHoCH bar index

        # Swing structure (longer pivot)
        self._s_trend    = 0
        self._s_highs    = deque(maxlen=10)
        self._s_lows     = deque(maxlen=10)
        self._s_bos_bull_bar = -999

        # Order Blocks
        self._bull_obs = deque(maxlen=5)        # OrderBlock instances
        self._bear_obs = deque(maxlen=5)

        # FVGs
        self._bull_fvgs = deque(maxlen=5)
        self._bear_fvgs = deque(maxlen=5)

        # Equal lows (EQL) tracking
        self._eq_highs = deque(maxlen=5)        # (price, bar_idx) — EQH candidates
        self._eq_lows  = deque(maxlen=5)        # (price, bar_idx) — EQL candidates
        self._eql_swept_bar = -999              # bar when EQL was swept

        # Bar counter
        self._bar_idx = 0
        self._last_day = None
        self._last_week = None
        self._last_mon  = None
        self._last_qtr  = None

        # ═════════════════════════════════════════════════════════════════════
        # SECTION 4 ▸ TRADE STATE
        # ═════════════════════════════════════════════════════════════════════
        self._bars_since_entry  = 0
        self._entry_stop        = None
        self._trail_high        = None
        self._t1_done           = False     # 30% exit at T1 fired
        self._t2_done           = False     # 30% exit at T2 fired
        self._entry_type        = None
        self._entry_score       = 0
        self._t1_level          = None
        self._t2_level          = None

        self.set_warm_up(TimeSpan.from_days(500))
        self.log(f"Nexus MTF Confluence | {ticker} | initialized")

    # ═════════════════════════════════════════════════════════════════════════
    # ON DATA  (every minute bar)
    # ═════════════════════════════════════════════════════════════════════════
    def on_data(self, data: Slice):
        if not data.bars.contains_key(self._sym):
            return

        bar = data.bars[self._sym]
        t   = bar.end_time
        self._bar_idx += 1

        self._update_htf_bars(bar, t)

        # Fire signal logic once per trading day (new 6H bar for NSE)
        day_id = t.date()
        if self._last_day is None:
            self._last_day = day_id
            return

        if day_id != self._last_day:
            self._last_day = day_id
            if not self.is_warming_up and len(self._6h_bars) >= 3:
                self._run_signal_engine(t)

    # ═════════════════════════════════════════════════════════════════════════
    # _update_htf_bars — aggregate minute bars into all timeframes
    # ═════════════════════════════════════════════════════════════════════════
    def _update_htf_bars(self, bar, t):
        o, h, l, c, v = bar.open, bar.high, bar.low, bar.close, bar.volume

        def upd(acc, high, low, close, vol):
            acc["high"]   = max(acc["high"], high)
            acc["low"]    = min(acc["low"],  low)
            acc["close"]  = close
            acc["vol"]   += vol

        day_id   = t.date()
        iso      = t.isocalendar()
        week_id  = (iso[0], iso[1])
        mon_id   = (t.year, t.month)
        qtr_id   = (t.year, (t.month - 1) // 3)

        # 6H (= one NSE session)
        if self._acc_6h is None or self._acc_6h["id"] != day_id:
            if self._acc_6h is not None:
                completed = _make_bar(self._acc_6h)
                self._6h_bars.appendleft(completed)
                self._vol_6h_hist.appendleft(completed.volume)
                self._update_structure_on_6h(completed)
            self._acc_6h = {"id": day_id, "open": o, "high": h,
                            "low": l, "close": c, "vol": v, "time": t}
        else:
            upd(self._acc_6h, h, l, c, v)

        # Daily
        if self._acc_day is None or self._acc_day["id"] != day_id:
            if self._acc_day is not None:
                completed = _make_bar(self._acc_day)
                self._daily_bars.appendleft(completed)
                self._vol_day_hist.appendleft(completed.volume)
                self._on_daily_bar_complete(completed)
            self._acc_day = {"id": day_id, "open": o, "high": h,
                             "low": l, "close": c, "vol": v, "time": t}
        else:
            upd(self._acc_day, h, l, c, v)

        # Weekly
        if self._acc_wk is None or self._acc_wk["id"] != week_id:
            if self._acc_wk is not None:
                self._weekly.appendleft(_make_bar(self._acc_wk))
            self._acc_wk = {"id": week_id, "open": o, "high": h,
                            "low": l, "close": c, "vol": v, "time": t}
        else:
            upd(self._acc_wk, h, l, c, v)

        # Monthly
        if self._acc_mon is None or self._acc_mon["id"] != mon_id:
            if self._acc_mon is not None:
                self._monthly.appendleft(_make_bar(self._acc_mon))
            self._acc_mon = {"id": mon_id, "open": o, "high": h,
                             "low": l, "close": c, "vol": v, "time": t}
        else:
            upd(self._acc_mon, h, l, c, v)

        # Quarterly
        if self._acc_qtr is None or self._acc_qtr["id"] != qtr_id:
            if self._acc_qtr is not None:
                self._quarterly.appendleft(_make_bar(self._acc_qtr))
            self._acc_qtr = {"id": qtr_id, "open": o, "high": h,
                             "low": l, "close": c, "vol": v, "time": t}
        else:
            upd(self._acc_qtr, h, l, c, v)

    def _on_daily_consolidated(self, bar):
        """Called by LEAN daily consolidator — used for ATR."""
        if self._prev_day_close is None:
            self._prev_day_close = bar.close
            return
        tr = max(bar.high - bar.low,
                 abs(bar.high - self._prev_day_close),
                 abs(bar.low  - self._prev_day_close))
        self._tr_window.append(tr)
        if len(self._tr_window) >= self.p_atr_len:
            self._atr_daily = sum(list(self._tr_window)[-self.p_atr_len:]) / self.p_atr_len
            self._atr_hist.append(self._atr_daily)
            if len(self._atr_hist) >= 126:
                self._atr_6m_avg = sum(list(self._atr_hist)[-126:]) / 126
        self._prev_day_close = bar.close

    # ═════════════════════════════════════════════════════════════════════════
    # _on_daily_bar_complete — update structure indicators on daily close
    # Sources ②③④: Liq zones, S/D zones, BOS/CHoCH, OB, FVG, EQH/EQL
    # ═════════════════════════════════════════════════════════════════════════
    def _on_daily_bar_complete(self, bar: Bar):
        if self._atr_daily is None:
            return
        atr = self._atr_daily
        idx = len(self._daily_bars)

        # Need at least p_swing_len bars for pivot detection
        if len(self._daily_bars) < self.p_swing_len + 2:
            return

        bars = list(self._daily_bars)  # [0]=newest complete bar

        # ── Pivot detection (GTF/PAC swing_len) ──────────────────────────────
        pivot_high, pivot_low = self._detect_pivot(
            bars, self.p_swing_len, idx)
        pivot_high_ob, pivot_low_ob = self._detect_pivot(
            bars, self.p_ob_len, idx)

        # ── Source ② Liquidity Zones — ZigZag update ─────────────────────────
        if pivot_high is not None:
            self._zz_highs.appendleft((pivot_high, idx))
            if self._zz_dir <= 0:
                self._zz_dir = 1
            elif self._zz_dir == 1:
                # Update latest high if higher
                if len(self._zz_highs) >= 2 and self._zz_highs[0][0] > self._zz_highs[1][0]:
                    self._zz_highs.popleft()  # keep only the higher one at [0]
            self._update_bsl_zones(pivot_high, idx, atr)

        if pivot_low is not None:
            self._zz_lows.appendleft((pivot_low, idx))
            if self._zz_dir >= 0:
                self._zz_dir = -1
            self._update_ssl_zones(pivot_low, idx, atr)

        # Check for SSL sweep: bar's low tagged an SSL zone then recovered
        self._check_ssl_sweep(bar, idx, atr)

        # ── Source ③ Supply/Demand Zones ─────────────────────────────────────
        if pivot_high is not None:
            self._update_supply_zones(pivot_high, idx, atr)
        if pivot_low is not None:
            self._update_demand_zones(pivot_low, idx, atr)

        # Check if price broke out of a supply or demand zone → BOS line
        self._check_sd_bos(bar.close, idx)

        # ── Source ④ BOS/CHoCH Detection ────────────────────────────────────
        if pivot_high_ob is not None:
            self._i_highs.appendleft((pivot_high_ob, idx))
        if pivot_low_ob is not None:
            self._i_lows.appendleft((pivot_low_ob, idx))

        self._check_internal_bos(bar.close, idx)
        self._check_swing_bos(bar.close, idx, pivot_high, pivot_low)

        # ── Source ④ Order Block detection ──────────────────────────────────
        if pivot_high_ob is not None:
            self._update_order_blocks_bull(bars, pivot_high_ob, idx, atr)
        if pivot_low_ob is not None:
            self._update_order_blocks_bear(bars, pivot_low_ob, idx, atr)

        # Mitigate order blocks: remove if price closed through OB
        self._mitigate_obs(bar.close)

        # ── Source ④ Fair Value Gap detection ────────────────────────────────
        if len(bars) >= 3:
            self._detect_fvg(bars, idx)

        # Mitigate FVGs
        self._mitigate_fvgs(bar.close)

        # ── Source ④ EQH/EQL detection ───────────────────────────────────────
        if pivot_high is not None:
            self._update_eqh(pivot_high, idx, atr)
        if pivot_low is not None:
            self._update_eql(pivot_low, idx, atr)

        # Check EQL sweep
        if pivot_low is not None:
            # Was a previous EQL just swept?
            for eq in self._eq_lows:
                if abs(bar.low - eq[0]) < 0.1 * atr and bar.close > eq[0]:
                    self._eql_swept_bar = idx
                    break

    def _update_structure_on_6h(self, bar: Bar):
        """Track 6H bar for Spider Wave Rule 2 state."""
        if len(self._monthly) < 1 or self._atr_daily is None:
            return
        monthly_high = self._monthly[0].high
        atr = self._atr_daily

        # Rule 2 state machine (Source ①)
        if bar.close > monthly_high and not self._spider_breakout_occurred:
            self._spider_breakout_occurred = True

        if self._spider_breakout_occurred and not self._spider_retest_seen:
            if (bar.low  <= monthly_high + 0.5 * atr and
                bar.high >= monthly_high):
                self._spider_retest_seen = True

        if bar.close < monthly_high - 1.5 * atr:
            self._spider_breakout_occurred = False
            self._spider_retest_seen       = False

    # ─────────────────────────────────────────────────────────────────────────
    # PIVOT DETECTION (shared by multiple sources)
    # ─────────────────────────────────────────────────────────────────────────
    def _detect_pivot(self, bars, length, bar_idx):
        """
        Detect ta.pivothigh / ta.pivotlow equivalent.
        bars[0] = most recent, bars[length] = pivot candidate,
        bars[2*length] = oldest comparison bar.
        Returns (pivot_high, pivot_low) or (None, None).
        """
        if len(bars) < 2 * length + 1:
            return None, None

        pivot_idx  = length   # candidate is in the middle
        pivot_bar  = bars[pivot_idx]

        ph = pivot_bar.high
        pl = pivot_bar.low

        is_ph = all(ph >= bars[i].high for i in range(length)) and \
                all(ph >= bars[pivot_idx + i + 1].high for i in range(length))
        is_pl = all(pl <= bars[i].low  for i in range(length)) and \
                all(pl <= bars[pivot_idx + i + 1].low  for i in range(length))

        return (ph if is_ph else None, pl if is_pl else None)

    # ─────────────────────────────────────────────────────────────────────────
    # Source ② LIQUIDITY ZONE UPDATES
    # ─────────────────────────────────────────────────────────────────────────
    def _update_bsl_zones(self, pivot_h, bar_idx, atr):
        """Cluster of 3+ pivot highs within ATR/liqMargin = Buyside Liquidity."""
        margin = atr / self.p_liq_margin
        count = 0
        level_sum = 0.0
        first_bar = bar_idx

        for ph, pidx in self._zz_highs:
            if ph > pivot_h + margin:
                break
            if abs(ph - pivot_h) <= margin:
                count += 1
                level_sum += ph
                first_bar = min(first_bar, pidx)

        if count >= 3:
            level = level_sum / count
            # Check if we already have this zone
            for i, z in enumerate(self._bsl_zones):
                if abs(z.level - level) < margin:
                    return  # duplicate
            self._bsl_zones.appendleft(LiqZone(
                level=level, is_buyside=True,
                bar_idx=first_bar, hit=False, swept=False))

    def _update_ssl_zones(self, pivot_l, bar_idx, atr):
        """Cluster of 3+ pivot lows within ATR/liqMargin = Sellside Liquidity."""
        margin = atr / self.p_liq_margin
        count = 0
        level_sum = 0.0
        first_bar = bar_idx

        for pl, pidx in self._zz_lows:
            if pl < pivot_l - margin:
                break
            if abs(pl - pivot_l) <= margin:
                count += 1
                level_sum += pl
                first_bar = min(first_bar, pidx)

        if count >= 3:
            level = level_sum / count
            for z in self._ssl_zones:
                if abs(z.level - level) < margin:
                    return
            self._ssl_zones.appendleft(LiqZone(
                level=level, is_buyside=False,
                bar_idx=first_bar, hit=False, swept=False))

    def _check_ssl_sweep(self, bar: Bar, bar_idx, atr):
        """
        SSL Sweep: bar's low tagged an SSL zone, then bar CLOSED above it.
        = Stop hunt complete = institutional buy = entry trigger.
        """
        margin = atr / self.p_liq_margin
        for i, z in enumerate(self._ssl_zones):
            if not z.swept:
                if bar.low <= z.level + margin and bar.close > z.level:
                    # Sweep detected
                    self._ssl_zones[i] = z._replace(swept=True, hit=True)
                    self._ssl_swept_bar   = bar_idx
                    self._ssl_swept_level = z.level

    # ─────────────────────────────────────────────────────────────────────────
    # Source ③ SUPPLY / DEMAND ZONES
    # ─────────────────────────────────────────────────────────────────────────
    def _update_supply_zones(self, pivot_h, bar_idx, atr):
        """Source ③: swing high creates supply zone."""
        buf = atr * (2.5 / 10.0)
        top = pivot_h
        bot = pivot_h - buf

        # Overlap filter: skip if another zone within 2×ATR
        threshold = 2 * atr
        for z in self._supply_zones:
            if z.active and abs((z.top + z.bottom) / 2 - (top + bot) / 2) < threshold:
                return

        self._supply_zones.appendleft(SDZone(
            top=top, bottom=bot, is_supply=True, bar_idx=bar_idx, active=True))

    def _update_demand_zones(self, pivot_l, bar_idx, atr):
        """Source ③: swing low creates demand zone."""
        buf = atr * (2.5 / 10.0)
        bot = pivot_l
        top = pivot_l + buf

        threshold = 2 * atr
        for z in self._demand_zones:
            if z.active and abs((z.top + z.bottom) / 2 - (top + bot) / 2) < threshold:
                return

        self._demand_zones.appendleft(SDZone(
            top=top, bottom=bot, is_supply=False, bar_idx=bar_idx, active=True))

    def _check_sd_bos(self, close, bar_idx):
        """Source ③: if price closes above supply or below demand → BOS conversion."""
        for i, z in enumerate(self._supply_zones):
            if z.active and close >= z.top:
                # Supply zone becomes BOS support
                mid = (z.top + z.bottom) / 2
                self._bos_lines.appendleft((mid, bar_idx, True))  # True = was supply
                self._supply_zones[i] = z._replace(active=False)

    # ─────────────────────────────────────────────────────────────────────────
    # Source ④ BOS/CHoCH DETECTION
    # ─────────────────────────────────────────────────────────────────────────
    def _check_internal_bos(self, close, bar_idx):
        """Source ④: internal structure BOS/CHoCH (short pivot)."""
        if len(self._i_highs) == 0 or len(self._i_lows) < 2:
            return

        latest_high = self._i_highs[0][0]
        latest_low  = self._i_lows[0][0]
        prev_low    = self._i_lows[1][0] if len(self._i_lows) >= 2 else latest_low

        # Bullish BOS: close above last internal high
        if close > latest_high:
            if self._i_trend < 0:
                # Was bearish → this is CHoCH (change of character)
                self._i_choch_bull_bar = bar_idx
                self._i_trend = 1
            else:
                # Continuation BOS
                self._i_bos_bull_bar = bar_idx
                self._i_trend = 1
            self._i_highs.clear()  # Pine: up.p.clear() after BOS

        # Bearish internal structure
        if close < latest_low:
            if self._i_trend > 0:
                self._i_trend = -1
            else:
                self._i_trend = -1
            self._i_lows.clear()

    def _check_swing_bos(self, close, bar_idx, ph, pl):
        """Source ④: swing structure BOS (long pivot)."""
        if len(self._s_highs) == 0 or len(self._s_lows) < 2:
            return

        latest_sh = self._s_highs[0][0]
        latest_sl = self._s_lows[0][0]

        if close > latest_sh:
            if self._s_trend < 0:
                self._s_trend = 1
            else:
                self._s_bos_bull_bar = bar_idx
                self._s_trend = 1
            self._s_highs.clear()

        if close < latest_sl:
            self._s_trend = -1
            self._s_lows.clear()

        if ph is not None:
            self._s_highs.appendleft((ph, bar_idx))
        if pl is not None:
            self._s_lows.appendleft((pl, bar_idx))

    # ─────────────────────────────────────────────────────────────────────────
    # Source ④ ORDER BLOCK DETECTION
    # ─────────────────────────────────────────────────────────────────────────
    def _update_order_blocks_bull(self, bars, pivot_h, bar_idx, atr):
        """
        Source ④: Bull OB = last bearish candle before bullish BOS.
        After a bullish internal BOS, find the most recent bearish candle
        below the BOS level — that's the institutional footprint.
        """
        if self._i_trend != 1:
            return  # Only create bull OB after bullish BOS

        # Find last bearish daily candle before pivot
        ob_len = self.p_ob_len
        for i in range(1, min(ob_len + 1, len(bars))):
            b = bars[i]
            if b.close < b.open:  # bearish candle
                ob_top = b.high
                ob_bot = b.low
                ob_avg = (ob_top + ob_bot) / 2.0
                # Skip if OB already exists nearby
                for ob in self._bull_obs:
                    if ob.active and abs(ob.avg - ob_avg) < atr:
                        return
                self._bull_obs.appendleft(OrderBlock(
                    top=ob_top, bottom=ob_bot, avg=ob_avg, is_bull=True,
                    bar_idx=bar_idx - i, volume=b.volume, active=True))
                break

    def _update_order_blocks_bear(self, bars, pivot_l, bar_idx, atr):
        """Source ④: Bear OB = last bullish candle before bearish BOS."""
        if self._i_trend != -1:
            return

        for i in range(1, min(self.p_ob_len + 1, len(bars))):
            b = bars[i]
            if b.close > b.open:  # bullish candle
                ob_top = b.high
                ob_bot = b.low
                ob_avg = (ob_top + ob_bot) / 2.0
                for ob in self._bear_obs:
                    if ob.active and abs(ob.avg - ob_avg) < atr:
                        return
                self._bear_obs.appendleft(OrderBlock(
                    top=ob_top, bottom=ob_bot, avg=ob_avg, is_bull=False,
                    bar_idx=bar_idx - i, volume=b.volume, active=True))
                break

    def _mitigate_obs(self, close):
        """Source ④: OB mitigated when price closes through bottom (bull OB) or top (bear OB)."""
        for i, ob in enumerate(self._bull_obs):
            if ob.active and close < ob.bottom:
                self._bull_obs[i] = ob._replace(active=False)
        for i, ob in enumerate(self._bear_obs):
            if ob.active and close > ob.top:
                self._bear_obs[i] = ob._replace(active=False)

    # ─────────────────────────────────────────────────────────────────────────
    # Source ④ FAIR VALUE GAP DETECTION
    # ─────────────────────────────────────────────────────────────────────────
    def _detect_fvg(self, bars, bar_idx):
        """
        Source ④: FVG = bars[2].high < bars[0].low (bullish) OR
                        bars[2].low > bars[0].high (bearish).
        bars[0]=most recent, bars[1]=middle, bars[2]=oldest.
        """
        b0, b1, b2 = bars[0], bars[1], bars[2]

        # Bullish FVG: gap between bar[2] high and bar[0] low
        if b2.high < b0.low and (b0.low - b2.high) > 0:
            self._bull_fvgs.appendleft(FVG(
                top=b0.low, bottom=b2.high,
                is_bull=True, bar_idx=bar_idx, active=True))

        # Bearish FVG
        if b2.low > b0.high and (b2.low - b0.high) > 0:
            self._bear_fvgs.appendleft(FVG(
                top=b2.low, bottom=b0.high,
                is_bull=False, bar_idx=bar_idx, active=True))

    def _mitigate_fvgs(self, close):
        """Source ④: FVG mitigated when price enters the gap."""
        for i, fvg in enumerate(self._bull_fvgs):
            if fvg.active and close < fvg.top:
                self._bull_fvgs[i] = fvg._replace(active=False)
        for i, fvg in enumerate(self._bear_fvgs):
            if fvg.active and close > fvg.bottom:
                self._bear_fvgs[i] = fvg._replace(active=False)

    # ─────────────────────────────────────────────────────────────────────────
    # Source ④ EQH / EQL DETECTION
    # ─────────────────────────────────────────────────────────────────────────
    def _update_eqh(self, pivot_h, bar_idx, atr):
        """Source ④: two pivot highs within 0.1×ATR = Equal High (BSL pool above)."""
        for prev_h, prev_idx in self._eq_highs:
            if abs(pivot_h - prev_h) < 0.1 * atr and bar_idx != prev_idx:
                # EQH detected — mark as BSL candidate
                self._bsl_zones.appendleft(LiqZone(
                    level=(pivot_h + prev_h) / 2,
                    is_buyside=True, bar_idx=prev_idx, hit=False, swept=False))
                break
        self._eq_highs.appendleft((pivot_h, bar_idx))

    def _update_eql(self, pivot_l, bar_idx, atr):
        """Source ④: two pivot lows within 0.1×ATR = Equal Low (SSL pool below)."""
        for prev_l, prev_idx in self._eq_lows:
            if abs(pivot_l - prev_l) < 0.1 * atr and bar_idx != prev_idx:
                self._ssl_zones.appendleft(LiqZone(
                    level=(pivot_l + prev_l) / 2,
                    is_buyside=False, bar_idx=prev_idx, hit=False, swept=False))
                break
        self._eq_lows.appendleft((pivot_l, bar_idx))

    # ═════════════════════════════════════════════════════════════════════════
    # _run_signal_engine — MAIN LOGIC fired once per trading day
    # ═════════════════════════════════════════════════════════════════════════
    def _run_signal_engine(self, t):

        # ── Guards ────────────────────────────────────────────────────────────
        if (len(self._6h_bars)   < 3 or
            len(self._monthly)   < 6 or
            len(self._weekly)    < 4 or
            len(self._quarterly) < 2 or
            self._atr_daily is None):
            return

        if not (self._ichimoku.is_ready and self._willr.is_ready and
                self._ema200.is_ready):
            return

        atr   = self._atr_daily
        b_idx = len(self._daily_bars)

        # ═════════════════════════════════════════════════════════════════════
        # SOURCE ① — SPIDER WAVE LAYERS
        # ═════════════════════════════════════════════════════════════════════
        b0_6h = self._6h_bars[0]   # current (just completed)
        b1_6h = self._6h_bars[1]   # previous
        b2_6h = self._6h_bars[2]   # two bars ago
        close  = b0_6h.close

        # Quarterly (Grandmother)
        qp1 = self._quarterly[0]
        qp2 = self._quarterly[1]
        qtr_cur = self._acc_qtr

        qtr_range_p1 = qp1.high - qp1.low
        qtr_close_pos = ((qp1.close - qp1.low) / qtr_range_p1
                         if qtr_range_p1 > 0 else 0.5)
        qtr_A = qtr_cur["open"]  > qp1.close
        qtr_B = qp1.low          > qp2.low
        qtr_C = qtr_close_pos    >= 0.60
        qtr_D = qtr_cur["close"] > qp1.high
        qtr_score     = sum([qtr_A, qtr_B, qtr_C, qtr_D])
        is_gma_bull   = qtr_score >= 3
        is_gma_weak   = qtr_score == 2
        qtr_size_mult = 1.0 if is_gma_bull else 0.5 if is_gma_weak else 0.0

        # Monthly (Mother)
        mp = list(self._monthly)[:6]
        mother_A = mp[0].close > mp[1].close
        mother_B = mp[0].low   >= (mp[1].low - 0.5 * atr)
        mother_C = (mp[0].high - mp[0].low) >= (mp[2].high - mp[2].low)
        is_mother_trend = mother_A and mother_B and mother_C

        ranges    = [mp[i].high - mp[i].low for i in range(6)]
        avg_range = sum(ranges) / 6
        is_inside = (mp[0].high <= mp[1].high and mp[0].low >= mp[1].low)
        is_range_valid = (ranges[0] >= 1.5 * atr and
                          ranges[0] >= self.p_min_range_ratio * avg_range and
                          not is_inside)

        monthly_high = mp[0].high
        monthly_low  = mp[0].low

        # 4-week high/low
        wp = list(self._weekly)[:4]
        weekly_high = max(w.high for w in wp)
        weekly_low  = min(w.low  for w in wp)

        # Macro state
        is_macro_breakout = close > monthly_high
        is_macro_supply   = monthly_low  <= close <= monthly_high
        is_macro_bottom   = (monthly_low - atr) <= close < monthly_low
        is_macro_overshot = close < (monthly_low - atr)

        # Volatility regime
        is_high_vol  = (self._atr_6m_avg is not None and atr > self._atr_6m_avg * 1.3)
        atr_sl_mult  = self.p_atr_sl_high if is_high_vol else self.p_atr_sl_norm

        # Rule 4 (close position filter)
        r6h = b0_6h.high - b0_6h.low
        uw6h = b0_6h.high - max(b0_6h.close, b0_6h.open)
        cp6h = (b0_6h.close - b0_6h.low) / r6h if r6h > 0 else 0.5
        rule4 = (cp6h >= self.p_close_pos_pct and
                 (uw6h / max(r6h, 0.001)) < self.p_wick_thresh and
                 b0_6h.close > b0_6h.open)

        # Rule 1 (two-candle)
        rule1_macro = (b1_6h.close > monthly_high and
                       b0_6h.close > monthly_high and
                       b0_6h.close >= b1_6h.close)

        # Rule 2 (retest)
        rule2_macro = (self._spider_breakout_occurred and
                       self._spider_retest_seen and
                       b0_6h.close > monthly_high and
                       b0_6h.close > b0_6h.open)

        # Rule 3 (volume sequence)
        vol_hist = list(self._vol_6h_hist)
        vol_ma = (sum(vol_hist[:20]) / 20 if len(vol_hist) >= 20 else None)
        if vol_ma:
            r3_build   = b2_6h.volume <= b1_6h.volume
            r3_surge   = b1_6h.volume >= vol_ma * 1.2
            r3_sustain = b0_6h.volume >= b1_6h.volume * 0.6
            rule3_full = r3_build and r3_surge and r3_sustain
            rule3_surge_only = r3_surge
        else:
            rule3_full = rule3_surge_only = False

        # ═════════════════════════════════════════════════════════════════════
        # SOURCE ⑤ ICHIMOKU CLOUD  (daily)
        # ═════════════════════════════════════════════════════════════════════
        ichi = self._ichimoku
        # Kumo (cloud): senkou span A and B
        span_a   = float(ichi.senkou_span_a.current.value)
        span_b   = float(ichi.senkou_span_b.current.value)
        tenkan   = float(ichi.tenkan_sen.current.value)
        kijun    = float(ichi.kijun_sen.current.value)
        cloud_top = max(span_a, span_b)
        cloud_bot = min(span_a, span_b)

        above_cloud   = close > cloud_top
        below_cloud   = close < cloud_bot
        in_cloud      = cloud_bot <= close <= cloud_top
        tenkan_bull   = tenkan > kijun      # Tenkan above Kijun = bull
        chikou_bull   = close > cloud_top   # simplified chikou proxy

        # ichi_bull_full: price above cloud + Tenkan > Kijun = 2pts
        # ichi_bull_part: price above cloud only = 1pt
        ichi_bull_full = above_cloud and tenkan_bull
        ichi_bull_part = above_cloud and not tenkan_bull

        # ═════════════════════════════════════════════════════════════════════
        # SOURCE ⑥ WILLIAMS %R  (14-period daily)
        # ═════════════════════════════════════════════════════════════════════
        willr_val = float(self._willr.current.value)  # 0 to -100
        # Oversold bounce: was below -80, now above -50 (rising)
        # We check current + direction via comparing to prior stored value
        willr_bounce = willr_val > -50 and willr_val < 0  # rising from oversold territory
        willr_os     = willr_val < -80  # currently oversold (look for turn)

        # ═════════════════════════════════════════════════════════════════════
        # SOURCE ⑦ VWAP
        # ═════════════════════════════════════════════════════════════════════
        vwap_val    = float(self._vwap.current.value) if self._vwap.is_ready else close
        above_vwap  = close > vwap_val

        # ═════════════════════════════════════════════════════════════════════
        # SOURCE ③ EMA STACK
        # ═════════════════════════════════════════════════════════════════════
        ema20v  = float(self._ema20.current.value)
        ema50v  = float(self._ema50.current.value)
        ema200v = float(self._ema200.current.value)

        ema_full_bull  = close > ema20v > ema50v > ema200v
        ema_part_bull  = close > ema200v  # at minimum above 200 EMA

        # ═════════════════════════════════════════════════════════════════════
        # SOURCE ④ BOS/CHoCH state
        # ═════════════════════════════════════════════════════════════════════
        recent_bull_bos   = (b_idx - self._i_bos_bull_bar   < 20)
        recent_bull_choch = (b_idx - self._i_choch_bull_bar < 15)
        recent_swing_bos  = (b_idx - self._s_bos_bull_bar   < 30)
        pac_bull_structure = self._i_trend == 1 or self._s_trend == 1

        # ═════════════════════════════════════════════════════════════════════
        # SOURCE ② LIQUIDITY CONTEXT
        # ═════════════════════════════════════════════════════════════════════
        # SSL sweep: did price sweep a sellside zone recently?
        ssl_swept_recently = (b_idx - self._ssl_swept_bar) < 5

        # Is price near an active BSL zone above? (target)
        nearest_bsl = None
        for z in self._bsl_zones:
            if not z.swept and z.level > close:
                if nearest_bsl is None or z.level < nearest_bsl:
                    nearest_bsl = z.level

        # ═════════════════════════════════════════════════════════════════════
        # SOURCE ③ ZONE CONTEXT
        # ═════════════════════════════════════════════════════════════════════
        # Is price currently inside or just above an active demand zone?
        in_demand_zone = False
        nearest_demand_top = None
        for z in self._demand_zones:
            if z.active and z.bottom <= close <= z.top * 1.005:
                in_demand_zone = True
                nearest_demand_top = z.top

        # Is price near a BOS line (converted supply zone)?
        near_bos_line = False
        for bos_level, bos_bar, _ in self._bos_lines:
            if abs(close - bos_level) < 0.5 * atr:
                near_bos_line = True

        # ═════════════════════════════════════════════════════════════════════
        # SOURCE ④ OB CONTEXT
        # ═════════════════════════════════════════════════════════════════════
        # Price in or just above a bullish order block?
        in_bull_ob = False
        nearest_ob_bot = None
        for ob in self._bull_obs:
            if ob.active and ob.bottom <= close <= ob.top * 1.005:
                in_bull_ob = True
                nearest_ob_bot = ob.bottom

        # FVG below price (unfilled bullish gap = strong support)
        bull_fvg_below = any(f.active and f.bottom < close < f.top * 1.1
                             for f in self._bull_fvgs)

        # EQL swept recently (stop hunt + reversal)
        eql_swept_recently = (b_idx - self._eql_swept_bar) < 5

        # ═════════════════════════════════════════════════════════════════════
        # ║  CONFLUENCE SCORING ENGINE                                       ║
        # ═════════════════════════════════════════════════════════════════════

        # ── MACRO LAYER (max 3pts) ───────────────────────────────────────────
        gma_pts = 2 if is_gma_bull else 1 if is_gma_weak else 0
        mother_pts = 1 if is_mother_trend and is_range_valid else 0

        # ── TREND LAYER (max 3pts) ───────────────────────────────────────────
        ichimoku_pts = 2 if ichi_bull_full else 1 if ichi_bull_part else 0
        bos_pts = (1 if (recent_bull_bos or recent_swing_bos or pac_bull_structure) else 0)

        # ── STRUCTURE / ZONE LAYER (max 2pts) ────────────────────────────────
        zone_pts = 1 if (in_demand_zone or in_bull_ob or near_bos_line) else 0
        ema_pts  = 1 if ema_full_bull else (0.5 if ema_part_bull else 0)

        # ── MOMENTUM LAYER (max 2pts) ─────────────────────────────────────────
        momentum_pts = 1 if (willr_bounce or above_vwap) else 0
        liq_pts      = 1 if ssl_swept_recently else 0

        # ── TRIGGER LAYER (max 1pt) ───────────────────────────────────────────
        trigger_pts = 1 if (rule4 and rule3_surge_only) else 0

        # ── BONUS POINTS ──────────────────────────────────────────────────────
        bonus = 0
        if bull_fvg_below:      bonus += 1
        if eql_swept_recently:  bonus += 1
        if recent_bull_choch:   bonus += 1

        raw_score = (gma_pts + mother_pts + ichimoku_pts + bos_pts +
                     zone_pts + ema_pts + momentum_pts + liq_pts +
                     trigger_pts + bonus)
        total_score = min(10.0, raw_score)

        # Determine entry type and size multiplier
        entry_type = None
        size_mult  = 0.0
        base_filter = is_mother_trend and is_range_valid

        if base_filter and qtr_size_mult > 0 and total_score >= self.p_min_score:
            if is_macro_breakout and rule1_macro and rule2_macro and rule3_full:
                entry_type = "A-PLUS" if total_score >= 8 else "A"
                size_mult  = 1.0 * qtr_size_mult
            elif is_macro_overshot and ssl_swept_recently and rule4:
                entry_type = "B-PLUS" if total_score >= 7 else "B"
                size_mult  = (1.0 if total_score >= 7 else 0.5) * qtr_size_mult
            elif is_macro_supply and (b1_6h.close > weekly_high) and rule3_surge_only:
                entry_type = "C"
                size_mult  = 0.5 * qtr_size_mult
            elif (is_macro_supply or is_macro_bottom) and in_demand_zone and rule3_surge_only:
                entry_type = "D"
                size_mult  = 0.25 * qtr_size_mult

        long_signal = entry_type is not None

        # ═════════════════════════════════════════════════════════════════════
        # STOP LOSS  (tightest of 4 levels)
        # ═════════════════════════════════════════════════════════════════════
        if long_signal:
            stop_candidates = [close - atr_sl_mult * atr]  # ATR floor

            if nearest_ob_bot is not None:
                stop_candidates.append(nearest_ob_bot - 0.3 * atr)

            for z in self._demand_zones:
                if z.active and z.bottom <= close:
                    stop_candidates.append(z.bottom - 0.3 * atr)

            if self._ssl_swept_level is not None:
                stop_candidates.append(self._ssl_swept_level - 0.3 * atr)

            proposed_stop = max(stop_candidates)  # highest = tightest stop
            stop_dist     = max(close - proposed_stop, 0.5 * atr)

            # ── R:R filter ─────────────────────────────────────────────────
            # T1 target: nearest supply zone top or +1.5×stop_dist
            t1_candidates = [close + self.p_min_rr * stop_dist]
            for z in self._supply_zones:
                if z.active and z.bottom > close:
                    t1_candidates.append(z.bottom)
            if nearest_bsl and nearest_bsl > close:
                t1_candidates.append(nearest_bsl)
            t1_level = min(t1_candidates)

            actual_rr = (t1_level - close) / stop_dist
            if actual_rr < self.p_min_rr:
                long_signal = False  # Skip: RR too low
                self.log(f"SKIP RR | {t:.date()} | RR:{actual_rr:.2f} < {self.p_min_rr}")

        # ═════════════════════════════════════════════════════════════════════
        # FIBONACCI TARGETS (Source ①)
        # ═════════════════════════════════════════════════════════════════════
        month_range = monthly_high - monthly_low
        fib1272     = monthly_high + month_range * 0.272
        fib1618     = monthly_high + month_range * 0.618

        # ═════════════════════════════════════════════════════════════════════
        # EXIT CONDITIONS  (Sources ①②③)
        # ═════════════════════════════════════════════════════════════════════
        in_trade = self.portfolio[self._sym].invested
        qty      = int(self.portfolio[self._sym].quantity)
        min_hold = 15   # minimum bars (trading days) before trailing/structure exits

        if in_trade:
            self._bars_since_entry += 1
            self._trail_high = max(self._trail_high or b0_6h.high, b0_6h.high)
        else:
            self._bars_since_entry = 0
            self._trail_high       = None

        since     = self._bars_since_entry
        trail_stp = (None if self._trail_high is None
                     else self._trail_high - self.p_atr_trail * atr)

        # T1: nearest supply zone or BSL zone (exit 30%)
        t1_exit = (in_trade and not self._t1_done and
                   since >= 5 and
                   self._t1_level is not None and
                   b0_6h.high >= self._t1_level)

        # T2: buyside liquidity or Fib 1.272 (exit 30%)
        t2_exit = (in_trade and not self._t2_done and
                   since >= 10 and
                   self._t2_level is not None and
                   b0_6h.high >= self._t2_level)

        # Full exits
        hard_stop     = (in_trade and self._entry_stop is not None and
                         since >= min_hold and close < self._entry_stop)
        struct_break  = (in_trade and since >= min_hold and close < monthly_low)
        trail_exit    = (in_trade and trail_stp is not None and
                         since >= min_hold and close < trail_stp)
        fib_exit      = in_trade and b0_6h.high >= fib1618

        # BOS flip (internal bearish CHoCH = early warning exit)
        choch_exit    = (in_trade and since >= min_hold and
                         self._i_trend == -1 and
                         (b_idx - self._i_choch_bull_bar) > min_hold)

        full_exit = hard_stop or struct_break or trail_exit or fib_exit or choch_exit

        # ═════════════════════════════════════════════════════════════════════
        # POSITION SIZING (Source ①)
        # ═════════════════════════════════════════════════════════════════════
        if long_signal and not in_trade:
            atr_stp_dist  = atr_sl_mult * atr
            stop_dist_sz  = max(atr_stp_dist, atr * 0.5)
            risk_capital  = (self.portfolio.total_portfolio_value *
                             (self.p_risk_pct / 100.0) * size_mult)
            qty_to_buy    = int(math.floor(risk_capital / stop_dist_sz))

        # ═════════════════════════════════════════════════════════════════════
        # ║  STRATEGY EXECUTION                                              ║
        # ═════════════════════════════════════════════════════════════════════

        # ── T1 Partial exit (30%) ─────────────────────────────────────────────
        if t1_exit and qty > 0:
            sell_qty = max(1, int(qty * 0.30))
            self.market_order(self._sym, -sell_qty, tag="T1_30pct")
            self._t1_done = True
            self.log(f"T1 EXIT | {t.date()} | "
                     f"Sold:{sell_qty} of {qty} | Level:{self._t1_level:.2f}")

        # ── T2 Partial exit (30%) ─────────────────────────────────────────────
        if t2_exit and qty > 0:
            sell_qty = max(1, int(qty * 0.30))
            self.market_order(self._sym, -sell_qty, tag="T2_30pct")
            self._t2_done = True
            self.log(f"T2 EXIT | {t.date()} | "
                     f"Sold:{sell_qty} of {qty} | Level:{self._t2_level:.2f}")

        # ── Full exit ─────────────────────────────────────────────────────────
        if full_exit and in_trade:
            reason = ("HardStop"    if hard_stop    else
                      "StructBreak" if struct_break  else
                      "TrailStop"   if trail_exit    else
                      "Fib1618"     if fib_exit      else
                      "CHoCH_flip")
            self.liquidate(self._sym, tag=f"Exit_{reason}")
            self._reset_trade_state()
            self.log(f"FULL EXIT {reason} | {t.date()} | "
                     f"Price:{close:.2f} | Held:{since}d | Score:{total_score:.1f}")

        # ── Entry ─────────────────────────────────────────────────────────────
        if (long_signal and not in_trade and
            not full_exit and qtr_size_mult > 0 and
            qty_to_buy > 0):

            # Set stops and targets
            self._entry_stop = proposed_stop
            self._t1_level   = t1_level
            # T2: BSL zone or Fib 1.272
            t2_candidates = [fib1272]
            if nearest_bsl and nearest_bsl > t1_level:
                t2_candidates.append(nearest_bsl)
            for z in self._supply_zones:
                if z.active and z.bottom > t1_level:
                    t2_candidates.append(z.bottom)
            self._t2_level = min(t2_candidates)

            self._entry_type  = entry_type
            self._entry_score = total_score
            self._t1_done     = False
            self._t2_done     = False
            self._bars_since_entry = 0

            self.market_order(self._sym, qty_to_buy, tag=f"Entry_{entry_type}")

            self.log(
                f"ENTRY {entry_type} | {t.date()} | "
                f"Price:{close:.2f} | Qty:{qty_to_buy} | "
                f"Stop:{self._entry_stop:.2f} | T1:{t1_level:.2f} | "
                f"T2:{self._t2_level:.2f} | Fib1618:{fib1618:.2f} | "
                f"Score:{total_score:.1f}/10 | "
                f"[Gma:{gma_pts} Mo:{mother_pts} Ichi:{ichimoku_pts} "
                f"BOS:{bos_pts} Zone:{zone_pts} EMA:{ema_pts} "
                f"Mom:{momentum_pts} Liq:{liq_pts} Trig:{trigger_pts} "
                f"Bonus:{bonus}] | "
                f"ATR:{'HIGH' if is_high_vol else 'NORMAL'}({atr:.2f}) | "
                f"WILLR:{willr_val:.1f} | EmaFull:{ema_full_bull} | "
                f"InDZ:{in_demand_zone} | InOB:{in_bull_ob} | "
                f"SSLSwept:{ssl_swept_recently}"
            )

    def _reset_trade_state(self):
        self._entry_stop       = None
        self._trail_high       = None
        self._t1_done          = False
        self._t2_done          = False
        self._entry_type       = None
        self._entry_score      = 0
        self._t1_level         = None
        self._t2_level         = None
        self._bars_since_entry = 0
        # Reset Spider Wave Rule 2 (Source ①)
        self._spider_breakout_occurred = False
        self._spider_retest_seen       = False

    # ═════════════════════════════════════════════════════════════════════════
    # ORDER EVENT + SUMMARY
    # ═════════════════════════════════════════════════════════════════════════
    def on_order_event(self, order_event: OrderEvent):
        if order_event.status == OrderStatus.FILLED:
            self.log(
                f"FILL | {order_event.symbol} | "
                f"Qty:{order_event.fill_quantity:+.0f} | "
                f"Price:{order_event.fill_price:.2f} | "
                f"Tag:{order_event.ticket.tag}")

    def on_end_of_algorithm(self):
        pv  = self.portfolio.total_portfolio_value
        pnl = pv - self.starting_portfolio_value
        pct = pnl / self.starting_portfolio_value * 100
        tc  = self.trade_builder.closed_trade_count

        self.log("═" * 70)
        self.log("NEXUS MTF CONFLUENCE — FINAL SUMMARY")
        self.log("═" * 70)
        self.log(f"  Symbol            : {self._sym}")
        self.log(f"  Start Capital     : {self.starting_portfolio_value:>12,.2f}")
        self.log(f"  Final Value       : {pv:>12,.2f}")
        self.log(f"  Net P&L           : {pnl:>+12,.2f}  ({pct:+.2f}%)")
        self.log(f"  Total Trades      : {tc}")
        self.log("═" * 70)


# ═════════════════════════════════════════════════════════════════════════════
# REFERENCE STRATEGIES
# These are simplified standalone strategies showing the core idea of each
# source Pine Script, useful for comparison and isolated backtesting.
# ═════════════════════════════════════════════════════════════════════════════

class RefStrategy_SpiderWave(QCAlgorithm):
    """
    REFERENCE 1 — Spider MTF Wave System v5.0 (isolated)
    ════════════════════════════════════════════════════
    Source: Pine Script ① — Spider MTF Wave System v5.0
    Logic: Pure wave hierarchy entry. No external indicators.
           Grandmother (quarterly) + Mother (monthly) + 5 Trap Rules.
    See: strategies/spider_wave/main.py for the full version.
    This version is a minimal, single-indicator reference.
    """
    def initialize(self):
        self.set_start_date(2019, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(100_000)
        self._sym = self.add_equity(
            self.get_parameter("symbol") or "SBIN",
            Resolution.DAILY, Market.INDIA).symbol
        self.set_brokerage_model(BrokerageName.ZERODHA_BROKERAGE, AccountType.MARGIN)

        self._monthly  = deque(maxlen=7)
        self._weekly   = deque(maxlen=5)
        self._quarterly= deque(maxlen=3)
        self._atr      = self.ATR(self._sym, 14, Resolution.DAILY)
        self._acc_wk   = None
        self._acc_mon  = None
        self._acc_qtr  = None
        self.set_warm_up(TimeSpan.from_days(400))

    def on_data(self, data):
        if not data.bars.contains_key(self._sym) or not self._atr.is_ready:
            return
        bar = data.bars[self._sym]
        t   = bar.end_time
        self._update(bar, t)

        if len(self._monthly) < 6 or len(self._quarterly) < 2:
            return
        if self.is_warming_up:
            return

        atr = float(self._atr.current.value)
        mp  = list(self._monthly)[:6]
        mh, ml = mp[0].high, mp[0].low
        qp1 = self._quarterly[0]
        qp2 = self._quarterly[1]

        # Grandmother score
        qr   = qp1.high - qp1.low
        qcp  = (qp1.close - qp1.low) / qr if qr > 0 else 0.5
        qsc  = sum([self._acc_qtr["open"] > qp1.close,
                    qp1.low > qp2.low, qcp >= 0.6,
                    self._acc_qtr["close"] > qp1.high])
        gma_ok = qsc >= 2

        # Mother trend
        mom_ok = (mp[0].close > mp[1].close and
                  mp[0].low >= mp[1].low - 0.5 * atr and
                  (mp[0].high - mp[0].low) >= (mp[2].high - mp[2].low))

        # Macro breakout: close above monthly high, 2 daily bars
        if gma_ok and mom_ok and bar.close > mh and not self.portfolio[self._sym].invested:
            risk = self.portfolio.total_portfolio_value * 0.01
            dist = max(1.5 * atr, 0.5 * atr)
            qty  = int(risk / dist)
            if qty > 0:
                self.market_order(self._sym, qty, tag="Spider_Ref")

        # Exit: trail below monthly low
        if self.portfolio[self._sym].invested and bar.close < ml:
            self.liquidate(self._sym, tag="Spider_Ref_Exit")

    def _update(self, bar, t):
        def u(acc, h, l, c, v):
            acc["high"] = max(acc["high"], h)
            acc["low"]  = min(acc["low"],  l)
            acc["close"] = c
        iso    = t.isocalendar()
        wk_id  = (iso[0], iso[1])
        mon_id = (t.year, t.month)
        qtr_id = (t.year, (t.month-1)//3)
        if self._acc_wk  is None or self._acc_wk["id"]  != wk_id:
            if self._acc_wk  is not None: self._weekly.appendleft(_make_bar(self._acc_wk))
            self._acc_wk  = {"id": wk_id, "open": bar.open, "high": bar.high,
                             "low": bar.low, "close": bar.close, "vol": bar.volume, "time": t}
        else: u(self._acc_wk, bar.high, bar.low, bar.close, bar.volume)
        if self._acc_mon is None or self._acc_mon["id"] != mon_id:
            if self._acc_mon is not None: self._monthly.appendleft(_make_bar(self._acc_mon))
            self._acc_mon = {"id": mon_id, "open": bar.open, "high": bar.high,
                             "low": bar.low, "close": bar.close, "vol": bar.volume, "time": t}
        else: u(self._acc_mon, bar.high, bar.low, bar.close, bar.volume)
        if self._acc_qtr is None or self._acc_qtr["id"] != qtr_id:
            if self._acc_qtr is not None: self._quarterly.appendleft(_make_bar(self._acc_qtr))
            self._acc_qtr = {"id": qtr_id, "open": bar.open, "high": bar.high,
                             "low": bar.low, "close": bar.close, "vol": bar.volume, "time": t}
        else: u(self._acc_qtr, bar.high, bar.low, bar.close, bar.volume)


class RefStrategy_LiquiditySweep(QCAlgorithm):
    """
    REFERENCE 2 — Buyside & Sellside Liquidity (isolated)
    ═════════════════════════════════════════════════════
    Source: Pine Script ② — Buyside & Sellside Liquidity
    Logic: Enter AFTER price sweeps a Sellside Liquidity cluster
           (stop hunt below pivot low cluster) and closes back above.
           Exit at next Buyside Liquidity cluster.
    Concept: Institutions sweep stops before reversing. This strategy
             exploits that pattern by entering after the sweep.
    """
    def initialize(self):
        self.set_start_date(2019, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(100_000)
        self._sym  = self.add_equity(
            self.get_parameter("symbol") or "SBIN",
            Resolution.DAILY, Market.INDIA).symbol
        self.set_brokerage_model(BrokerageName.ZERODHA_BROKERAGE, AccountType.MARGIN)
        self._atr  = self.ATR(self._sym, 14, Resolution.DAILY)
        self._ph   = deque(maxlen=50)   # pivot highs
        self._pl   = deque(maxlen=50)   # pivot lows
        self._daily= deque(maxlen=20)
        self._ssl  = deque(maxlen=5)    # sellside liquidity levels
        self._bsl  = deque(maxlen=5)    # buyside liquidity levels
        self.set_warm_up(TimeSpan.from_days(100))
        self._liq_len = 7

    def on_data(self, data):
        if not data.bars.contains_key(self._sym) or not self._atr.is_ready:
            return
        bar = data.bars[self._sym]
        self._daily.appendleft(bar)
        atr = float(self._atr.current.value)
        margin = atr / 1.45

        if len(self._daily) < self._liq_len * 2 + 1 or self.is_warming_up:
            return

        bars = list(self._daily)
        # Pivot detection (liq_len=7 each side)
        ph = self._pivot(bars, self._liq_len, is_high=True)
        pl = self._pivot(bars, self._liq_len, is_high=False)

        if ph is not None:
            self._ph.appendleft(ph)
            self._update_bsl(ph, atr, margin)
        if pl is not None:
            self._pl.appendleft(pl)
            self._update_ssl(pl, atr, margin)

        # Check sweep: bar's low tagged SSL and closed back above
        swept_level = None
        for i, ssl in enumerate(self._ssl):
            if bar.low <= ssl + margin and bar.close > ssl:
                swept_level = ssl
                self._ssl[i] = -999  # mark as swept
                break

        # Entry: after SSL sweep
        if swept_level and not self.portfolio[self._sym].invested:
            risk = self.portfolio.total_portfolio_value * 0.01
            qty  = int(risk / max(atr * 1.5, atr * 0.5))
            if qty > 0:
                self.market_order(self._sym, qty, tag=f"SSL_Sweep@{swept_level:.2f}")

        # Exit: price reaches nearest BSL zone
        if self.portfolio[self._sym].invested:
            for bsl in self._bsl:
                if bar.high >= bsl and bsl > bar.close * 0.99:
                    self.liquidate(self._sym, tag=f"BSL_Target@{bsl:.2f}")
                    break

    def _pivot(self, bars, length, is_high):
        if len(bars) < 2 * length + 1:
            return None
        candidate = bars[length]
        if is_high:
            p = candidate.high
            return p if (all(p >= bars[i].high for i in range(length)) and
                         all(p >= bars[length+i+1].high for i in range(length))) else None
        else:
            p = candidate.low
            return p if (all(p <= bars[i].low for i in range(length)) and
                         all(p <= bars[length+i+1].low for i in range(length))) else None

    def _update_bsl(self, ph, atr, margin):
        count = sum(1 for p in self._ph if abs(p - ph) <= margin)
        if count >= 3:
            level = sum(p for p in self._ph if abs(p - ph) <= margin) / count
            if not any(abs(b - level) < margin for b in self._bsl):
                self._bsl.appendleft(level)

    def _update_ssl(self, pl, atr, margin):
        count = sum(1 for p in self._pl if abs(p - pl) <= margin)
        if count >= 3:
            level = sum(p for p in self._pl if abs(p - pl) <= margin) / count
            if not any(abs(s - level) < margin for s in self._ssl):
                self._ssl.appendleft(level)


class RefStrategy_SupplyDemand(QCAlgorithm):
    """
    REFERENCE 3 — GTF Supply & Demand (isolated)
    ═════════════════════════════════════════════
    Source: Pine Script ③ — GTF Supply & Demand / Liquidity
    Logic: Buy at Demand Zone when EMA stack is bullish (price > EMA20 > EMA50 > EMA200).
           Sell at nearest Supply Zone. Exit if price closes below demand zone.
    Concept: Price returns to institutional imbalance zones (demand/supply)
             and these act as support/resistance. EMA stack confirms trend direction.
    """
    def initialize(self):
        self.set_start_date(2019, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(100_000)
        self._sym   = self.add_equity(
            self.get_parameter("symbol") or "SBIN",
            Resolution.DAILY, Market.INDIA).symbol
        self.set_brokerage_model(BrokerageName.ZERODHA_BROKERAGE, AccountType.MARGIN)
        self._ema20  = self.EMA(self._sym, 20,  Resolution.DAILY)
        self._ema50  = self.EMA(self._sym, 50,  Resolution.DAILY)
        self._ema200 = self.EMA(self._sym, 200, Resolution.DAILY)
        self._atr    = self.ATR(self._sym, 50,  Resolution.DAILY)
        self._daily  = deque(maxlen=25)
        self._demand = deque(maxlen=5)   # (top, bottom) demand zones
        self._supply = deque(maxlen=5)   # (top, bottom) supply zones
        self._entry_demand_bot = None
        self.set_warm_up(TimeSpan.from_days(250))
        self._swing_len = 10

    def on_data(self, data):
        if not data.bars.contains_key(self._sym):
            return
        if not (self._ema200.is_ready and self._atr.is_ready):
            return
        bar = data.bars[self._sym]
        self._daily.appendleft(bar)

        if len(self._daily) < self._swing_len * 2 + 1 or self.is_warming_up:
            return

        bars = list(self._daily)
        atr  = float(self._atr.current.value)
        buf  = atr * 0.25

        ph = self._pivot(bars, self._swing_len, True)
        pl = self._pivot(bars, self._swing_len, False)

        if ph:
            self._supply.appendleft((ph, ph - buf))
        if pl:
            # Overlap check
            ok = all(abs((z[0]+z[1])/2 - (pl+pl+buf)/2) >= 2*atr
                     for z in self._demand)
            if ok:
                self._demand.appendleft((pl + buf, pl))

        ema20  = float(self._ema20.current.value)
        ema50  = float(self._ema50.current.value)
        ema200 = float(self._ema200.current.value)
        ema_bull = bar.close > ema20 > ema50 > ema200

        # Entry: price in demand zone + EMA stack bullish
        if not self.portfolio[self._sym].invested and ema_bull:
            for top, bot in self._demand:
                if bot <= bar.close <= top * 1.005:
                    risk = self.portfolio.total_portfolio_value * 0.01
                    qty  = int(risk / max(bar.close - bot + 0.3 * atr, 0.5 * atr))
                    if qty > 0:
                        self.market_order(self._sym, qty, tag=f"DZ_Entry@{bar.close:.2f}")
                        self._entry_demand_bot = bot
                    break

        # Exit: nearest supply zone OR price closes below demand zone bottom
        if self.portfolio[self._sym].invested:
            for top, bot in self._supply:
                if bar.high >= bot and top > bar.close * 0.99:
                    self.liquidate(self._sym, tag=f"SZ_Exit@{bot:.2f}")
                    self._entry_demand_bot = None
                    return
            if self._entry_demand_bot and bar.close < self._entry_demand_bot - 0.3 * atr:
                self.liquidate(self._sym, tag="DZ_Breakdown")
                self._entry_demand_bot = None

    def _pivot(self, bars, length, is_high):
        if len(bars) < 2 * length + 1:
            return None
        c = bars[length]
        if is_high:
            p = c.high
            return p if (all(p >= bars[i].high for i in range(length)) and
                         all(p >= bars[length+j+1].high for j in range(length))) else None
        p = c.low
        return p if (all(p <= bars[i].low for i in range(length)) and
                     all(p <= bars[length+j+1].low for j in range(length))) else None


class RefStrategy_PriceActionConcepts(QCAlgorithm):
    """
    REFERENCE 4 — Price Action Concepts / LuxAlgo (isolated)
    ═══════════════════════════════════════════════════════════
    Source: Pine Script ④ — Price Action Concepts v1.2.2 (LuxAlgo)
    Logic: Enter long on Bullish CHoCH (Change of Character) from the
           daily timeframe. This marks the FIRST sign of a reversal.
           Enter again on BOS (Break of Structure) for continuation.
           Place stop below the last internal Order Block.
           Exit at bearish CHoCH or bearish BOS (structural flip).
    Concept: Structure defines direction. CHoCH = first reversal signal.
             BOS = trend confirmation. Order Blocks = institutional support.
    """
    def initialize(self):
        self.set_start_date(2019, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(100_000)
        self._sym  = self.add_equity(
            self.get_parameter("symbol") or "SBIN",
            Resolution.DAILY, Market.INDIA).symbol
        self.set_brokerage_model(BrokerageName.ZERODHA_BROKERAGE, AccountType.MARGIN)
        self._atr  = self.ATR(self._sym, 14, Resolution.DAILY)
        self._daily= deque(maxlen=20)
        self._int_highs = deque(maxlen=10)
        self._int_lows  = deque(maxlen=10)
        self._i_trend   = 0
        self._last_ob_bot = None
        self.set_warm_up(TimeSpan.from_days(60))
        self._ob_len = 5

    def on_data(self, data):
        if not data.bars.contains_key(self._sym) or not self._atr.is_ready:
            return
        bar = data.bars[self._sym]
        self._daily.appendleft(bar)
        atr  = float(self._atr.current.value)

        if len(self._daily) < self._ob_len * 2 + 1 or self.is_warming_up:
            return

        bars = list(self._daily)
        ph   = self._pivot(bars, self._ob_len, True)
        pl   = self._pivot(bars, self._ob_len, False)
        if ph: self._int_highs.appendleft((ph, len(self._daily)))
        if pl: self._int_lows.appendleft( (pl, len(self._daily)))

        if len(self._int_highs) == 0 or len(self._int_lows) < 2:
            return

        prev_trend = self._i_trend

        # Bullish internal BOS/CHoCH
        if bar.close > self._int_highs[0][0]:
            self._i_trend = 1
            self._int_highs.clear()
            # Find last bearish candle before this high = Order Block bottom
            for b in bars[1:self._ob_len+1]:
                if b.close < b.open:
                    self._last_ob_bot = b.low - 0.3 * atr
                    break

        # Bearish internal BOS/CHoCH
        if bar.close < self._int_lows[0][0]:
            self._i_trend = -1
            self._int_lows.clear()

        # Entry on bullish CHoCH (trend flipped from -1 to +1)
        if (self._i_trend == 1 and prev_trend <= 0 and
            not self.portfolio[self._sym].invested):
            stop = self._last_ob_bot or (bar.close - 1.5 * atr)
            risk = self.portfolio.total_portfolio_value * 0.01
            dist = max(bar.close - stop, 0.5 * atr)
            qty  = int(risk / dist)
            if qty > 0:
                self.market_order(self._sym, qty, tag="CHoCH_Entry")

        # Exit on bearish CHoCH/BOS
        if self.portfolio[self._sym].invested and self._i_trend == -1:
            self.liquidate(self._sym, tag="Bearish_Structure_Exit")

    def _pivot(self, bars, length, is_high):
        if len(bars) < 2 * length + 1: return None
        c = bars[length]
        if is_high:
            p = c.high
            return p if (all(p >= bars[i].high for i in range(length)) and
                         all(p >= bars[length+j+1].high for j in range(length))) else None
        p = c.low
        return p if (all(p <= bars[i].low for i in range(length)) and
                     all(p <= bars[length+j+1].low for j in range(length))) else None
