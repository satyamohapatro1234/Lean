"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         NEXUS F&O STRATEGY — NSE Futures & Options                         ║
║         Two-Sided: Long via Futures/Calls | Short via Futures/Puts         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  COMPANION TO: NexusMTFConfluenceStrategy (equity, long-only)              ║
║                                                                              ║
║  INSTRUMENTS:                                                                ║
║    • Futures → both long AND short (overnight positions)                    ║
║    • Equity  → long only (no overnight shorts in cash NSE)                  ║
║                                                                              ║
║  SAME INDICATORS AS EQUITY STRATEGY:                                        ║
║  ① Spider MTF Wave v5.0   — macro wave hierarchy + trap rules               ║
║  ② Buyside/Sellside Liq   — stop cluster detection + sweep signals         ║
║  ③ GTF Supply & Demand    — EMA stack + S/D zones                          ║
║  ④ Price Action Concepts  — BOS/CHoCH + Order Blocks + FVG                 ║
║  ⑤ Ichimoku Cloud         — daily trend gate                                ║
║  ⑥ Williams %R            — oversold/overbought momentum                    ║
║  ⑦ VWAP                   — value area bias                                 ║
║                                                                              ║
║  ADDED FOR F&O:                                                              ║
║  • Mirror SHORT scoring (bearish versions of all 7 layers)                  ║
║  • Lot-size aware sizing (NIFTY=25, BANKNIFTY=30, FINNIFTY=40, etc.)       ║
║  • Expiry management (exit 2 days before last Thursday)                     ║
║  • Bearish signal types: A-SHORT, B-SHORT, C-SHORT, D-SHORT                ║
║  • BSL sweep rejection (price spikes above BSL → reversal short)           ║
║                                                                              ║
║  SCORING (same 10-pt system, but mirrored for shorts):                     ║
║  LONG  signals: same as equity strategy                                     ║
║  SHORT signals: bear macro + bear trend + supply zone + overbought          ║
╚══════════════════════════════════════════════════════════════════════════════╝

NSE-SPECIFIC NOTES:
  • Futures lot sizes (post-Dec 2024):
      NIFTY=25, BANKNIFTY=30, FINNIFTY=40, MIDCPNIFTY=75
      Individual stocks: see LOT_SIZES dict below
  • Weekly expiry: ONLY NIFTY & SENSEX (post Nov 2024)
  • Monthly expiry: last Thursday of the month
  • STT on options exercise: 0.1% of intrinsic value (post Oct 2024)
  • Margins: ~10-15% of notional for futures (SPAN + exposure)

Python 3.11 required (.venv311)
Run: python engine-wrapper/run_backtest.py --config strategies/nexus_fno/lean-config.json
"""

from AlgorithmImports import *
from collections import deque, namedtuple
import math

# ─────────────────────────────────────────────────────────────────────────────
# Data structures (shared with equity strategy)
# ─────────────────────────────────────────────────────────────────────────────
Bar   = namedtuple("Bar",   ["open","high","low","close","volume","time"])
SDZone= namedtuple("SDZone",["top","bottom","is_supply","bar_idx","active"])
OB    = namedtuple("OB",    ["top","bottom","avg","is_bull","bar_idx","volume","active"])
FVG   = namedtuple("FVG",   ["top","bottom","is_bull","bar_idx","active"])
LiqZ  = namedtuple("LiqZ",  ["level","is_buyside","bar_idx","swept"])

def _bar(acc):
    return Bar(acc["open"],acc["high"],acc["low"],
               acc["close"],acc["vol"],acc.get("time"))

# ─────────────────────────────────────────────────────────────────────────────
# NSE Lot sizes (post-Dec 2024, update as SEBI revises)
# ─────────────────────────────────────────────────────────────────────────────
LOT_SIZES = {
    "NIFTY":       25,   "BANKNIFTY":   30,   "FINNIFTY":    40,
    "MIDCPNIFTY":  75,   "SENSEX":      10,   "BANKEX":      15,
    "RELIANCE":   250,   "TCS":         150,   "INFY":        300,
    "HDFCBANK":   550,   "ICICIBANK":   700,   "SBIN":       1500,
    "AXISBANK":   625,   "KOTAKBANK":   400,   "LT":         275,
    "ITC":       1600,   "HINDUNILVR":  300,   "BAJFINANCE":  125,
    "WIPRO":      900,   "ADANIENT":    325,   "TATAMOTORS":  900,
    "TATASTEEL": 2700,   "MARUTI":       45,   "TITAN":       375,
    "ASIANPAINT": 300,   "ULTRACEMCO":  100,   "TECHM":       600,
    "NTPC":      3750,   "POWERGRID":  3750,   "ONGC":       1925,
    "COALINDIA": 2100,   "SUNPHARMA":   350,   "DRREDDY":    125,
}

def get_lot_size(symbol_str: str) -> int:
    """Return lot size for a given NSE symbol. Default 1 lot = 1 share if unknown."""
    return LOT_SIZES.get(symbol_str.upper().split(" ")[0], 1)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN F&O ALGORITHM
# ─────────────────────────────────────────────────────────────────────────────
class NexusFnOStrategy(QCAlgorithm):
    """
    Nexus F&O Strategy — two-sided (long + short) for NSE futures.
    Uses same 10-point confluence scoring as equity strategy,
    mirrored for bear signals.
    """

    def initialize(self):
        self.set_start_date(2019, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(500_000)

        ticker    = self.get_parameter("symbol") or "SBIN"
        self._sym = self.add_equity(ticker, Resolution.MINUTE, Market.INDIA).symbol
        self._ticker = ticker.upper()

        # For actual futures, you would use:
        # self._future = self.add_future(ticker, Resolution.MINUTE, Market.INDIA)
        # But since LEAN India futures data setup varies, we simulate
        # futures P&L using equity with margin = lot_size × margin_pct
        # This gives identical signal logic; replace with AddFuture when data ready.
        self.set_brokerage_model(BrokerageName.ZERODHA_BROKERAGE, AccountType.MARGIN)

        # Lot size
        self._lot = get_lot_size(self._ticker)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 0 ▸ PARAMETERS
        # ══════════════════════════════════════════════════════════════════════
        self.p_risk_pct      = float(self.get_parameter("risk_pct")      or "1.5")
        self.p_atr_len       = int(self.get_parameter("atr_len")          or "14")
        self.p_atr_sl_norm   = float(self.get_parameter("atr_sl_norm")   or "1.2")  # tighter for F&O
        self.p_atr_sl_high   = float(self.get_parameter("atr_sl_high")   or "2.0")
        self.p_atr_trail     = float(self.get_parameter("atr_trail")     or "2.0")
        self.p_min_rr        = float(self.get_parameter("min_rr")        or "1.5")
        self.p_min_score_l   = int(self.get_parameter("min_score_long")  or "6")
        self.p_min_score_s   = int(self.get_parameter("min_score_short") or "6")
        self.p_swing_len     = int(self.get_parameter("swing_len")       or "10")
        self.p_ob_len        = int(self.get_parameter("ob_len")          or "5")
        self.p_liq_margin    = float(self.get_parameter("liq_margin")    or "1.45")
        self.p_min_range_ratio=float(self.get_parameter("min_range_ratio")or "0.70")

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 1 ▸ HTF BAR ACCUMULATORS
        # ══════════════════════════════════════════════════════════════════════
        self._6h      = deque(maxlen=6)
        self._daily   = deque(maxlen=300)
        self._weekly  = deque(maxlen=8)
        self._monthly = deque(maxlen=8)
        self._qtr     = deque(maxlen=5)
        self._acc_6h  = self._acc_day = self._acc_wk = None
        self._acc_mon = self._acc_qtr = None
        self._vol_6h  = deque(maxlen=25)
        self._prev_close = None
        self._tr_win     = deque(maxlen=20)
        self._atr_daily  = None
        self._atr_hist   = deque(maxlen=200)
        self._atr_6m     = None

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 2 ▸ LEAN BUILT-IN INDICATORS
        # ══════════════════════════════════════════════════════════════════════
        self.consolidate(self._sym, Resolution.DAILY, self._on_daily_bar)

        self._ichimoku = IchimokuKinkoHyo(9, 26, 52, 26, 52, 26)
        self.register_indicator(self._sym, self._ichimoku, Resolution.DAILY)

        self._willr  = WilliamPercentR(14)
        self.register_indicator(self._sym, self._willr, Resolution.DAILY)

        self._vwap   = IntradayVwap()
        self.register_indicator(self._sym, self._vwap, Resolution.MINUTE)

        self._ema20  = ExponentialMovingAverage(20)
        self._ema50  = ExponentialMovingAverage(50)
        self._ema200 = ExponentialMovingAverage(200)
        for ind in [self._ema20, self._ema50, self._ema200]:
            self.register_indicator(self._sym, ind, Resolution.DAILY)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 3 ▸ STRUCTURE STATE — LONG SIDE
        # ══════════════════════════════════════════════════════════════════════
        self._demand_zones  = deque(maxlen=5)
        self._supply_zones  = deque(maxlen=5)
        self._bull_obs      = deque(maxlen=5)
        self._bear_obs      = deque(maxlen=5)
        self._bull_fvgs     = deque(maxlen=5)
        self._bear_fvgs     = deque(maxlen=5)
        self._ssl_zones     = deque(maxlen=5)
        self._bsl_zones     = deque(maxlen=5)
        self._piv_highs     = deque(maxlen=50)
        self._piv_lows      = deque(maxlen=50)
        self._i_highs       = deque(maxlen=10)
        self._i_lows        = deque(maxlen=10)
        self._i_trend       = 0
        self._s_highs       = deque(maxlen=10)
        self._s_lows        = deque(maxlen=10)
        self._s_trend       = 0
        self._i_bos_bull    = -999
        self._i_choch_bull  = -999
        self._i_bos_bear    = -999
        self._i_choch_bear  = -999
        self._ssl_swept_bar = -999
        self._ssl_swept_lvl = None
        self._bsl_swept_bar = -999   # ← SHORT: BSL sweep rejection
        self._bsl_swept_lvl = None
        self._eql_swept_bar = -999
        self._eqh_swept_bar = -999   # ← SHORT: equal highs swept
        self._eq_lows       = deque(maxlen=5)
        self._eq_highs      = deque(maxlen=5)
        self._spider_bo_occ = False
        self._spider_rt_seen= False
        self._bar_idx       = 0
        self._last_day      = None

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 4 ▸ TRADE STATE (separate for long and short)
        # ══════════════════════════════════════════════════════════════════════
        # Long trade state
        self._L_active      = False
        self._L_entry_stop  = None
        self._L_t1          = None
        self._L_t2          = None
        self._L_t1_done     = False
        self._L_t2_done     = False
        self._L_trail_high  = None
        self._L_bars        = 0
        self._L_entry_type  = None
        self._L_lots        = 0

        # Short trade state
        self._S_active      = False
        self._S_entry_stop  = None   # stop is ABOVE entry for shorts
        self._S_t1          = None
        self._S_t2          = None
        self._S_t1_done     = False
        self._S_t2_done     = False
        self._S_trail_low   = None   # lowest price since entry (for trail)
        self._S_bars        = 0
        self._S_entry_type  = None
        self._S_lots        = 0

        self.set_warm_up(TimeSpan.from_days(500))
        self.log(f"Nexus F&O | {ticker} | Lot:{self._lot} | initialized")

    # ══════════════════════════════════════════════════════════════════════════
    # ON DATA
    # ══════════════════════════════════════════════════════════════════════════
    def on_data(self, data: Slice):
        if not data.bars.contains_key(self._sym):
            return
        bar = data.bars[self._sym]
        t   = bar.end_time
        self._bar_idx += 1
        self._update_htf(bar, t)

        day = t.date()
        if self._last_day is None:
            self._last_day = day
            return
        if day != self._last_day:
            self._last_day = day
            if not self.is_warming_up and len(self._6h) >= 3:
                self._run(t)

    # ══════════════════════════════════════════════════════════════════════════
    # HTF BAR ACCUMULATION
    # ══════════════════════════════════════════════════════════════════════════
    def _update_htf(self, bar, t):
        o,h,l,c,v = bar.open,bar.high,bar.low,bar.close,bar.volume
        def u(a,H,L,C,V): a["high"]=max(a["high"],H);a["low"]=min(a["low"],L);a["close"]=C;a["vol"]+=V
        day_id=(t.date()); iso=t.isocalendar(); wk_id=(iso[0],iso[1])
        mon_id=(t.year,t.month); qtr_id=(t.year,(t.month-1)//3)

        for acc_ref, id_val, store in [
            ("_acc_6h",  day_id,  self._6h),
            ("_acc_wk",  wk_id,   self._weekly),
            ("_acc_mon", mon_id,  self._monthly),
            ("_acc_qtr", qtr_id,  self._qtr),
        ]:
            acc = getattr(self, acc_ref)
            if acc is None or acc["id"] != id_val:
                if acc is not None:
                    completed = _bar(acc)
                    store.appendleft(completed)
                    if acc_ref == "_acc_6h":
                        self._vol_6h.appendleft(completed.volume)
                setattr(self, acc_ref, {"id":id_val,"open":o,"high":h,
                                         "low":l,"close":c,"vol":v,"time":t})
            else:
                u(acc,h,l,c,v)

        if self._acc_day is None or self._acc_day["id"] != day_id:
            if self._acc_day is not None:
                comp = _bar(self._acc_day)
                self._daily.appendleft(comp)
                self._on_daily_struct(comp)
            self._acc_day = {"id":day_id,"open":o,"high":h,
                             "low":l,"close":c,"vol":v,"time":t}
        else:
            u(self._acc_day,h,l,c,v)

    def _on_daily_bar(self, bar):
        """ATR computation via LEAN consolidator."""
        if self._prev_close is None:
            self._prev_close = bar.close; return
        tr = max(bar.high-bar.low,
                 abs(bar.high-self._prev_close),
                 abs(bar.low -self._prev_close))
        self._tr_win.append(tr)
        if len(self._tr_win) >= self.p_atr_len:
            self._atr_daily = sum(list(self._tr_win)[-self.p_atr_len:])/self.p_atr_len
            self._atr_hist.append(self._atr_daily)
            if len(self._atr_hist) >= 126:
                self._atr_6m = sum(list(self._atr_hist)[-126:])/126
        self._prev_close = bar.close

    # ══════════════════════════════════════════════════════════════════════════
    # DAILY STRUCTURE ENGINE  (runs on each completed daily bar)
    # ══════════════════════════════════════════════════════════════════════════
    def _on_daily_struct(self, bar: Bar):
        if self._atr_daily is None or len(self._daily) < self.p_swing_len*2+1:
            return
        atr  = self._atr_daily
        bars = list(self._daily)
        idx  = len(self._daily)
        mg   = atr / self.p_liq_margin

        ph, pl = self._pivot(bars, self.p_swing_len)
        ph_ob, pl_ob = self._pivot(bars, self.p_ob_len)

        # ── Pivot history ─────────────────────────────────────────────────────
        if ph is not None: self._piv_highs.appendleft((ph, idx))
        if pl is not None: self._piv_lows.appendleft((pl, idx))

        # ── Source ② Liquidity zones ─────────────────────────────────────────
        if ph is not None: self._upd_bsl(ph, idx, mg)
        if pl is not None: self._upd_ssl(pl, idx, mg)

        # Check SSL sweep (bull trigger)
        if bar.low <= min((z.level for z in self._ssl_zones if not z.swept),
                          default=float("inf")) + mg and \
           bar.close > min((z.level for z in self._ssl_zones if not z.swept),
                           default=float("inf")):
            for i,z in enumerate(self._ssl_zones):
                if not z.swept and bar.low <= z.level+mg and bar.close > z.level:
                    self._ssl_zones[i]=z._replace(swept=True)
                    self._ssl_swept_bar=idx; self._ssl_swept_lvl=z.level

        # Check BSL sweep rejection (bear trigger — price spikes above BSL then closes below)
        for i,z in enumerate(self._bsl_zones):
            if not z.swept and bar.high >= z.level-mg and bar.close < z.level:
                self._bsl_zones[i]=z._replace(swept=True)
                self._bsl_swept_bar=idx; self._bsl_swept_lvl=z.level

        # ── Source ③ S/D zones ────────────────────────────────────────────────
        if ph is not None:
            buf=atr*0.25; top=ph; bot=ph-buf
            thr=2*atr
            if all(abs((z.top+z.bottom)/2-(top+bot)/2)>=thr
                   for z in self._supply_zones if z.active):
                self._supply_zones.appendleft(SDZone(top,bot,True,idx,True))

        if pl is not None:
            buf=atr*0.25; bot=pl; top=pl+buf
            thr=2*atr
            if all(abs((z.top+z.bottom)/2-(top+bot)/2)>=thr
                   for z in self._demand_zones if z.active):
                self._demand_zones.appendleft(SDZone(top,bot,False,idx,True))

        # Mitigate S/D zones (price closes through them)
        for i,z in enumerate(self._demand_zones):
            if z.active and bar.close < z.bottom:
                self._demand_zones[i]=z._replace(active=False)
        for i,z in enumerate(self._supply_zones):
            if z.active and bar.close > z.top:
                self._supply_zones[i]=z._replace(active=False)

        # ── Source ④ BOS/CHoCH ─────────────────────────────────────────────
        if ph_ob is not None: self._i_highs.appendleft((ph_ob,idx))
        if pl_ob is not None: self._i_lows.appendleft( (pl_ob,idx))

        if self._i_highs and self._i_lows and len(self._i_lows)>=2:
            latest_h = self._i_highs[0][0]
            latest_l = self._i_lows[0][0]
            prev_l   = self._i_lows[1][0]
            prev_h   = self._i_highs[1][0] if len(self._i_highs)>=2 else latest_h

            if bar.close > latest_h:          # BULLISH BOS / CHoCH
                if self._i_trend < 0:
                    self._i_choch_bull = idx
                else:
                    self._i_bos_bull   = idx
                self._i_trend = 1
                self._i_highs.clear()
                # Bull OB: last bearish candle before this high
                for b in bars[1:self.p_ob_len+1]:
                    if b.close < b.open:
                        avg=(b.high+b.low)/2
                        if not any(abs(o.avg-avg)<atr for o in self._bull_obs if o.active):
                            self._bull_obs.appendleft(OB(b.high,b.low,avg,True,idx-1,b.volume,True))
                        break

            if bar.close < latest_l:          # BEARISH BOS / CHoCH
                if self._i_trend > 0:
                    self._i_choch_bear = idx
                else:
                    self._i_bos_bear   = idx
                self._i_trend = -1
                self._i_lows.clear()
                # Bear OB: last bullish candle before this low
                for b in bars[1:self.p_ob_len+1]:
                    if b.close > b.open:
                        avg=(b.high+b.low)/2
                        if not any(abs(o.avg-avg)<atr for o in self._bear_obs if o.active):
                            self._bear_obs.appendleft(OB(b.high,b.low,avg,False,idx-1,b.volume,True))
                        break

        # Mitigate OBs
        for i,o in enumerate(self._bull_obs):
            if o.active and bar.close < o.bottom: self._bull_obs[i]=o._replace(active=False)
        for i,o in enumerate(self._bear_obs):
            if o.active and bar.close > o.top:   self._bear_obs[i]=o._replace(active=False)

        # ── Source ④ FVG ──────────────────────────────────────────────────────
        if len(bars) >= 3:
            b0,b1,b2=bars[0],bars[1],bars[2]
            if b2.high < b0.low:
                self._bull_fvgs.appendleft(FVG(b0.low,b2.high,True,idx,True))
            if b2.low > b0.high:
                self._bear_fvgs.appendleft(FVG(b2.low,b0.high,False,idx,True))
        for i,f in enumerate(self._bull_fvgs):
            if f.active and bar.close < f.top: self._bull_fvgs[i]=f._replace(active=False)
        for i,f in enumerate(self._bear_fvgs):
            if f.active and bar.close > f.bottom: self._bear_fvgs[i]=f._replace(active=False)

        # ── Source ④ EQH / EQL ───────────────────────────────────────────────
        if pl is not None:
            for prev_l, prev_idx in self._eq_lows:
                if abs(pl-prev_l) < 0.1*atr:
                    lvl=(pl+prev_l)/2
                    self._ssl_zones.appendleft(LiqZ(lvl,False,prev_idx,False))
                    break
            self._eq_lows.appendleft((pl,idx))

        if ph is not None:
            for prev_h, prev_idx in self._eq_highs:
                if abs(ph-prev_h) < 0.1*atr:
                    lvl=(ph+prev_h)/2
                    self._bsl_zones.appendleft(LiqZ(lvl,True,prev_idx,False))
                    break
            self._eq_highs.appendleft((ph,idx))

        # ── Spider Wave Rule 2 state ──────────────────────────────────────────
        if len(self._monthly) >= 1:
            mh = self._monthly[0].high
            if bar.close > mh and not self._spider_bo_occ:
                self._spider_bo_occ = True
            if self._spider_bo_occ and not self._spider_rt_seen:
                if bar.low <= mh+0.5*atr and bar.high >= mh:
                    self._spider_rt_seen = True
            if bar.close < mh-1.5*atr:
                self._spider_bo_occ=False; self._spider_rt_seen=False

    # ══════════════════════════════════════════════════════════════════════════
    # EXPIRY MANAGEMENT
    # "Exit futures positions 2 trading days before the last Thursday"
    # ══════════════════════════════════════════════════════════════════════════
    def _is_expiry_week(self, t) -> bool:
        """Returns True if we are within 2 trading days of last Thursday of month."""
        import calendar
        year, month = t.year, t.month
        # Find last Thursday of this month
        last_day = calendar.monthrange(year, month)[1]
        for d in range(last_day, last_day-7, -1):
            import datetime
            dt = datetime.date(year, month, d)
            if dt.weekday() == 3:  # Thursday
                last_thu = dt
                break
        days_to_expiry = (last_thu - t.date()).days
        return 0 <= days_to_expiry <= 2

    # ══════════════════════════════════════════════════════════════════════════
    # MAIN SIGNAL ENGINE  (runs once per trading day)
    # ══════════════════════════════════════════════════════════════════════════
    def _run(self, t):
        if (len(self._6h) < 3 or len(self._monthly) < 6 or
            len(self._weekly) < 4 or len(self._qtr) < 2 or
            self._atr_daily is None or not self._ichimoku.is_ready or
            not self._willr.is_ready or not self._ema200.is_ready):
            return

        atr   = self._atr_daily
        idx   = len(self._daily)

        # ── Expiry check: close futures positions early ───────────────────────
        if self._is_expiry_week(t):
            if self._L_active:
                self.liquidate(self._sym, tag="Expiry_Roll_Long")
                self._reset_long()
                self.log(f"EXPIRY ROLL (Long) | {t.date()}")
            if self._S_active:
                self.liquidate(self._sym, tag="Expiry_Roll_Short")
                self._reset_short()
                self.log(f"EXPIRY ROLL (Short) | {t.date()}")
            return

        b0 = self._6h[0]; b1 = self._6h[1]; b2 = self._6h[2]
        close = b0.close

        # ── Spider Wave layers ────────────────────────────────────────────────
        qp1 = self._qtr[0]; qp2 = self._qtr[1]; qc = self._acc_qtr
        qr   = qp1.high-qp1.low
        qcp  = (qp1.close-qp1.low)/qr if qr>0 else 0.5
        qsc  = sum([qc["open"]>qp1.close, qp1.low>qp2.low,
                    qcp>=0.6, qc["close"]>qp1.high])
        is_gma_bull = qsc >= 3
        is_gma_weak = qsc == 2
        is_gma_bear = qsc <= 1   # ← SHORT condition
        q_mult      = 1.0 if is_gma_bull else 0.5 if is_gma_weak else 0.0
        q_mult_s    = 1.0 if is_gma_bear else 0.0  # short only when macro weak/bear

        mp   = list(self._monthly)[:6]
        mo_A = mp[0].close > mp[1].close
        mo_B = mp[0].low   >= mp[1].low - 0.5*atr
        mo_C = (mp[0].high-mp[0].low) >= (mp[2].high-mp[2].low)
        is_mother_bull = mo_A and mo_B and mo_C
        is_mother_bear = not mo_A and not mo_B  # lower close + lower low

        rngs   = [mp[i].high-mp[i].low for i in range(6)]
        avg_rng= sum(rngs)/6
        inside = mp[0].high<=mp[1].high and mp[0].low>=mp[1].low
        rng_ok = rngs[0]>=1.5*atr and rngs[0]>=self.p_min_range_ratio*avg_rng and not inside

        mh = mp[0].high; ml = mp[0].low
        wp = list(self._weekly)[:4]
        wh = max(w.high for w in wp); wl = min(w.low for w in wp)

        is_macro_breakout = close > mh
        is_macro_supply   = ml <= close <= mh
        is_macro_bottom   = (ml-atr) <= close < ml
        is_macro_overshot = close < (ml-atr)
        is_macro_breakdown= close < (ml-atr)     # same as overshot for shorts

        # Volatility
        is_hv   = (self._atr_6m and atr > self._atr_6m*1.3)
        sl_mult = self.p_atr_sl_high if is_hv else self.p_atr_sl_norm

        # Rule 4 (LONG)
        r6h = b0.high-b0.low
        uw  = b0.high-max(b0.close,b0.open)
        cp  = (b0.close-b0.low)/r6h if r6h>0 else 0.5
        rule4_l = cp>=0.70 and (uw/max(r6h,0.001))<0.30 and b0.close>b0.open

        # Rule 4 (SHORT — mirror: close in BOTTOM 30%, small lower wick)
        lw   = min(b0.close,b0.open)-b0.low
        cp_s = (b0.high-b0.close)/r6h if r6h>0 else 0.5
        rule4_s = cp_s>=0.70 and (lw/max(r6h,0.001))<0.30 and b0.close<b0.open

        # Rule 1 (two-candle)
        rule1_l = (b1.close>mh and b0.close>mh and b0.close>=b1.close)
        rule1_s = (b1.close<ml and b0.close<ml and b0.close<=b1.close)

        # Rule 2
        rule2_l = (self._spider_bo_occ and self._spider_rt_seen and
                   b0.close>mh and b0.close>b0.open)

        # Rule 3 (volume sequence)
        vh = list(self._vol_6h)
        vm = (sum(vh[:20])/20 if len(vh)>=20 else None)
        if vm:
            r3_l = b2.volume<=b1.volume and b1.volume>=vm*1.2 and b0.volume>=b1.volume*0.6
            r3_s = b2.volume<=b1.volume and b1.volume>=vm*1.2 and b0.volume>=b1.volume*0.6
            r3_surge = b1.volume>=vm*1.2
        else:
            r3_l=r3_s=r3_surge=False

        # ── Ichimoku ─────────────────────────────────────────────────────────
        span_a = float(self._ichimoku.senkou_span_a.current.value)
        span_b = float(self._ichimoku.senkou_span_b.current.value)
        tenkan = float(self._ichimoku.tenkan_sen.current.value)
        kijun  = float(self._ichimoku.kijun_sen.current.value)
        ct,cb  = max(span_a,span_b), min(span_a,span_b)

        ichi_l_full = close>ct and tenkan>kijun         # price above cloud + T>K
        ichi_l_part = close>ct and not tenkan>kijun     # price above cloud only
        ichi_s_full = close<cb and tenkan<kijun         # price below cloud + T<K (SHORT)
        ichi_s_part = close<cb and not tenkan<kijun     # price below cloud only

        # ── Williams %R ──────────────────────────────────────────────────────
        wr = float(self._willr.current.value)
        willr_bounce  = wr>-50 and wr<0           # rising from oversold
        willr_topout  = wr>-20                    # overbought → potential reversal

        # ── VWAP ─────────────────────────────────────────────────────────────
        vwap_v   = float(self._vwap.current.value) if self._vwap.is_ready else close
        abv_vwap = close>vwap_v
        blw_vwap = close<vwap_v

        # ── EMA stack ────────────────────────────────────────────────────────
        e20=float(self._ema20.current.value)
        e50=float(self._ema50.current.value)
        e200=float(self._ema200.current.value)
        ema_bull_full  = close>e20>e50>e200
        ema_bear_full  = close<e20<e50<e200      # SHORT
        ema_part_bull  = close>e200
        ema_part_bear  = close<e200

        # ── Structure context (LONG) ──────────────────────────────────────────
        in_dz = any(z.active and z.bottom<=close<=z.top*1.005 for z in self._demand_zones)
        in_ob = any(o.active and o.bottom<=close<=o.top*1.005 for o in self._bull_obs)
        fvg_bl= any(f.active and f.bottom<close<f.top*1.1 for f in self._bull_fvgs)
        ssl_sw= (idx-self._ssl_swept_bar)<5
        eql_sw= (idx-self._eql_swept_bar)<5
        bos_l = self._i_trend==1 or (idx-self._i_bos_bull)<20
        choch_l=(idx-self._i_choch_bull)<15

        # ── Structure context (SHORT) ─────────────────────────────────────────
        in_sz  = any(z.active and z.bottom<=close<=z.top*1.005 for z in self._supply_zones)
        in_bob = any(o.active and o.bottom<=close<=o.top*1.005 for o in self._bear_obs)
        fvg_br = any(f.active and f.bottom*0.9<close<f.top for f in self._bear_fvgs)
        bsl_sw = (idx-self._bsl_swept_bar)<5     # BSL sweep rejection
        eqh_sw = (idx-self._eqh_swept_bar)<5
        bos_s  = self._i_trend==-1 or (idx-self._i_bos_bear)<20
        choch_s= (idx-self._i_choch_bear)<15

        # Nearest BSL and SSL
        bsl_lvl = min((z.level for z in self._bsl_zones if not z.swept and z.level>close), default=None)
        ssl_lvl = max((z.level for z in self._ssl_zones if not z.swept and z.level<close), default=None)

        # ══════════════════════════════════════════════════════════════════════
        # ║  LONG CONFLUENCE SCORE  (same as equity strategy)               ║
        # ══════════════════════════════════════════════════════════════════════
        gma_l  = 2 if is_gma_bull else 1 if is_gma_weak else 0
        mo_l   = 1 if (is_mother_bull and rng_ok) else 0
        ichi_l = 2 if ichi_l_full else 1 if ichi_l_part else 0
        bos_l_pts = 1 if bos_l else 0
        zone_l = 1 if (in_dz or in_ob) else 0
        ema_l  = 1 if ema_bull_full else (0.5 if ema_part_bull else 0)
        mom_l  = 1 if (willr_bounce or abv_vwap) else 0
        liq_l  = 1 if ssl_sw else 0
        trig_l = 1 if (rule4_l and r3_surge) else 0
        bon_l  = (1 if fvg_bl else 0)+(1 if eql_sw else 0)+(1 if choch_l else 0)
        score_l = min(10.0, gma_l+mo_l+ichi_l+bos_l_pts+zone_l+ema_l+mom_l+liq_l+trig_l+bon_l)

        # ══════════════════════════════════════════════════════════════════════
        # ║  SHORT CONFLUENCE SCORE  (mirror of long)                       ║
        # ══════════════════════════════════════════════════════════════════════
        # Grandmother: bear = qsc<=1 = 2pts; weak = qsc==2 = 1pt
        gma_s  = 2 if is_gma_bear else (1 if is_gma_weak else 0)
        mo_s   = 1 if (is_mother_bear and rng_ok) else 0
        ichi_s = 2 if ichi_s_full else 1 if ichi_s_part else 0
        bos_s_pts = 1 if bos_s else 0
        zone_s = 1 if (in_sz or in_bob) else 0
        ema_s  = 1 if ema_bear_full else (0.5 if ema_part_bear else 0)
        mom_s  = 1 if (willr_topout or blw_vwap) else 0
        liq_s  = 1 if bsl_sw else 0     # BSL sweep rejection = shorts' version of SSL sweep
        trig_s = 1 if (rule4_s and r3_surge) else 0
        bon_s  = (1 if fvg_br else 0)+(1 if eqh_sw else 0)+(1 if choch_s else 0)
        score_s = min(10.0, gma_s+mo_s+ichi_s+bos_s_pts+zone_s+ema_s+mom_s+liq_s+trig_s+bon_s)

        # ══════════════════════════════════════════════════════════════════════
        # ║  ENTRY TYPE DETERMINATION                                       ║
        # ══════════════════════════════════════════════════════════════════════
        base_f_l = (is_mother_bull and rng_ok)
        base_f_s = rng_ok  # for shorts, mother_bear OR just range valid

        # LONG entry types
        long_type = None; long_mult = 0.0
        if base_f_l and q_mult>0 and score_l>=self.p_min_score_l:
            if is_macro_breakout and rule1_l and rule2_l and r3_l:
                long_type="A-PLUS" if score_l>=8 else "A"; long_mult=1.0*q_mult
            elif is_macro_overshot and ssl_sw and rule4_l:
                long_type="B-PLUS" if score_l>=7 else "B"; long_mult=(1.0 if score_l>=7 else 0.5)*q_mult
            elif is_macro_supply and b1.close>wh and r3_surge:
                long_type="C"; long_mult=0.5*q_mult
            elif (is_macro_supply or is_macro_bottom) and in_dz and r3_surge:
                long_type="D"; long_mult=0.25*q_mult

        # SHORT entry types (mirror)
        short_type = None; short_mult = 0.0
        if base_f_s and score_s>=self.p_min_score_s:
            if is_macro_breakdown and rule1_s and r3_s:
                short_type="A-SHORT" if score_s>=8 else "B-SHORT"; short_mult=1.0
            elif bsl_sw and rule4_s and in_sz:
                short_type="BSL-SHORT" if score_s>=7 else "C-SHORT"; short_mult=(1.0 if score_s>=7 else 0.5)
            elif is_macro_supply and b1.close<wl and r3_surge:
                short_type="D-SHORT"; short_mult=0.5
            # Scale by Grandmother bear score
            short_mult *= (1.0 if is_gma_bear else 0.5)

        long_signal  = long_type  is not None
        short_signal = short_type is not None

        # ══════════════════════════════════════════════════════════════════════
        # ║  STOP LEVELS & RR CHECK                                         ║
        # ══════════════════════════════════════════════════════════════════════
        if long_signal:
            stop_l_cands = [close - sl_mult*atr]
            if in_ob:
                for o in self._bull_obs:
                    if o.active and o.bottom<=close: stop_l_cands.append(o.bottom-0.3*atr)
            for z in self._demand_zones:
                if z.active and z.bottom<=close: stop_l_cands.append(z.bottom-0.3*atr)
            stop_l   = max(stop_l_cands)
            dist_l   = max(close-stop_l, 0.5*atr)
            # T1: nearest supply zone or +1.5×dist
            t1_l_cands = [close+self.p_min_rr*dist_l]
            for z in self._supply_zones:
                if z.active and z.bottom>close: t1_l_cands.append(z.bottom)
            if bsl_lvl: t1_l_cands.append(bsl_lvl)
            t1_l = min(t1_l_cands)
            if (t1_l-close)/dist_l < self.p_min_rr:
                long_signal=False
                self.log(f"SKIP LONG RR | {t.date()} | RR:{(t1_l-close)/dist_l:.2f}")

        if short_signal:
            stop_s_cands = [close + sl_mult*atr]   # stop ABOVE for short
            if in_bob:
                for o in self._bear_obs:
                    if o.active and o.top>=close: stop_s_cands.append(o.top+0.3*atr)
            for z in self._supply_zones:
                if z.active and z.top>=close: stop_s_cands.append(z.top+0.3*atr)
            stop_s   = min(stop_s_cands)           # tightest = lowest stop above
            dist_s   = max(stop_s-close, 0.5*atr)
            # T1: nearest demand zone or -1.5×dist
            t1_s_cands = [close-self.p_min_rr*dist_s]
            for z in self._demand_zones:
                if z.active and z.top<close: t1_s_cands.append(z.top)
            if ssl_lvl: t1_s_cands.append(ssl_lvl)
            t1_s = max(t1_s_cands)                 # highest demand zone below
            if (close-t1_s)/dist_s < self.p_min_rr:
                short_signal=False
                self.log(f"SKIP SHORT RR | {t.date()} | RR:{(close-t1_s)/dist_s:.2f}")

        # ══════════════════════════════════════════════════════════════════════
        # ║  FIBONACCI TARGETS                                               ║
        # ══════════════════════════════════════════════════════════════════════
        mrange  = mh-ml
        fib_l_1272 = mh + mrange*0.272
        fib_l_1618 = mh + mrange*0.618
        fib_s_1272 = ml - mrange*0.272   # short targets below monthly low
        fib_s_1618 = ml - mrange*0.618

        # ══════════════════════════════════════════════════════════════════════
        # ║  EXIT CONDITIONS — LONG                                         ║
        # ══════════════════════════════════════════════════════════════════════
        min_hold = 10  # F&O holds shorter — min 10 trading days

        if self._L_active:
            self._L_bars += 1
            self._L_trail_high = max(self._L_trail_high or b0.high, b0.high)
        trail_l = (None if self._L_trail_high is None
                   else self._L_trail_high - self.p_atr_trail*atr)

        qty_l = int(self.portfolio[self._sym].quantity)
        qty_l = max(0, qty_l)

        t1_hit_l = (self._L_active and not self._L_t1_done and
                    self._L_bars>=5 and self._L_t1 and b0.high>=self._L_t1)
        t2_hit_l = (self._L_active and not self._L_t2_done and
                    self._L_bars>=8 and self._L_t2 and b0.high>=self._L_t2)

        hard_sl_l   = self._L_active and self._L_entry_stop and self._L_bars>=min_hold and close<self._L_entry_stop
        struct_l    = self._L_active and self._L_bars>=min_hold and close<ml
        trail_ex_l  = self._L_active and trail_l and self._L_bars>=min_hold and close<trail_l
        fib_ex_l    = self._L_active and b0.high>=fib_l_1618
        choch_ex_l  = self._L_active and self._i_trend==-1 and self._L_bars>=min_hold

        full_exit_l = hard_sl_l or struct_l or trail_ex_l or fib_ex_l or choch_ex_l

        # ══════════════════════════════════════════════════════════════════════
        # ║  EXIT CONDITIONS — SHORT                                        ║
        # ══════════════════════════════════════════════════════════════════════
        if self._S_active:
            self._S_bars += 1
            self._S_trail_low = min(self._S_trail_low or b0.low, b0.low)
        trail_s = (None if self._S_trail_low is None
                   else self._S_trail_low + self.p_atr_trail*atr)

        qty_s = abs(int(self.portfolio[self._sym].quantity)) if qty_l==0 else 0

        t1_hit_s = (self._S_active and not self._S_t1_done and
                    self._S_bars>=5 and self._S_t1 and b0.low<=self._S_t1)
        t2_hit_s = (self._S_active and not self._S_t2_done and
                    self._S_bars>=8 and self._S_t2 and b0.low<=self._S_t2)

        hard_sl_s  = self._S_active and self._S_entry_stop and self._S_bars>=min_hold and close>self._S_entry_stop
        struct_s   = self._S_active and self._S_bars>=min_hold and close>mh
        trail_ex_s = self._S_active and trail_s and self._S_bars>=min_hold and close>trail_s
        fib_ex_s   = self._S_active and b0.low<=fib_s_1618
        choch_ex_s = self._S_active and self._i_trend==1 and self._S_bars>=min_hold

        full_exit_s = hard_sl_s or struct_s or trail_ex_s or fib_ex_s or choch_ex_s

        # ══════════════════════════════════════════════════════════════════════
        # ║  POSITION SIZING (lot-aware)                                    ║
        # ══════════════════════════════════════════════════════════════════════
        def _lots_to_buy(dist, mult, is_short=False):
            risk   = self.portfolio.total_portfolio_value*(self.p_risk_pct/100)*mult
            dist_f = max(dist, 0.5*atr)
            shares = math.floor(risk/dist_f)
            lots   = max(1, shares//self._lot)
            return lots * self._lot

        # ══════════════════════════════════════════════════════════════════════
        # ║  EXECUTIONS                                                     ║
        # ══════════════════════════════════════════════════════════════════════

        # ── Long T1 / T2 partials ──────────────────────────────────────────
        if t1_hit_l and qty_l>0:
            sell=max(self._lot, (qty_l*30//100//self._lot)*self._lot)
            self.market_order(self._sym,-sell,tag="L_T1_30pct")
            self._L_t1_done=True
            self.log(f"LONG T1 | {t.date()} | -{sell} | Level:{self._L_t1:.2f}")

        if t2_hit_l and qty_l>0:
            sell=max(self._lot, (qty_l*30//100//self._lot)*self._lot)
            self.market_order(self._sym,-sell,tag="L_T2_30pct")
            self._L_t2_done=True
            self.log(f"LONG T2 | {t.date()} | -{sell} | Level:{self._L_t2:.2f}")

        # ── Long full exit ─────────────────────────────────────────────────
        if full_exit_l and self._L_active:
            reason=("HardStop" if hard_sl_l else "StructBreak" if struct_l
                    else "TrailStop" if trail_ex_l else "Fib1618" if fib_ex_l
                    else "BearCHoCH")
            self.liquidate(self._sym, tag=f"L_Exit_{reason}")
            self._reset_long()
            self.log(f"LONG EXIT {reason} | {t.date()} | Price:{close:.2f} | "
                     f"Held:{self._L_bars}d | Score:{score_l:.1f}")

        # ── Short T1 / T2 partials ─────────────────────────────────────────
        if t1_hit_s and self._S_active:
            cover=max(self._lot,(qty_s*30//100//self._lot)*self._lot)
            self.market_order(self._sym,+cover,tag="S_T1_30pct")  # buy to cover
            self._S_t1_done=True
            self.log(f"SHORT T1 | {t.date()} | +{cover} | Level:{self._S_t1:.2f}")

        if t2_hit_s and self._S_active:
            cover=max(self._lot,(qty_s*30//100//self._lot)*self._lot)
            self.market_order(self._sym,+cover,tag="S_T2_30pct")
            self._S_t2_done=True
            self.log(f"SHORT T2 | {t.date()} | +{cover} | Level:{self._S_t2:.2f}")

        # ── Short full exit ────────────────────────────────────────────────
        if full_exit_s and self._S_active:
            reason=("HardStop" if hard_sl_s else "StructBreak" if struct_s
                    else "TrailStop" if trail_ex_s else "Fib1618" if fib_ex_s
                    else "BullCHoCH")
            self.liquidate(self._sym, tag=f"S_Exit_{reason}")
            self._reset_short()
            self.log(f"SHORT EXIT {reason} | {t.date()} | Price:{close:.2f} | "
                     f"Held:{self._S_bars}d | Score:{score_s:.1f}")

        # ── LONG ENTRY ─────────────────────────────────────────────────────
        if (long_signal and not self._L_active and not self._S_active and
            not full_exit_l and long_mult>0):

            dist_sz = max(close-stop_l, 0.5*atr)
            qty_buy = _lots_to_buy(dist_sz, long_mult)

            # T2 target
            t2_l_cands = [fib_l_1272]
            if bsl_lvl and bsl_lvl>t1_l: t2_l_cands.append(bsl_lvl)
            for z in self._supply_zones:
                if z.active and z.bottom>t1_l: t2_l_cands.append(z.bottom)
            t2_l = min(t2_l_cands)

            self._L_active=True; self._L_entry_stop=stop_l
            self._L_t1=t1_l; self._L_t2=t2_l
            self._L_t1_done=False; self._L_t2_done=False
            self._L_trail_high=None; self._L_bars=0
            self._L_entry_type=long_type; self._L_lots=qty_buy//self._lot

            self.market_order(self._sym, qty_buy, tag=f"L_Entry_{long_type}")
            self.log(
                f"LONG {long_type} | {t.date()} | "
                f"Price:{close:.2f} | Qty:{qty_buy}({self._L_lots}lots) | "
                f"Stop:{stop_l:.2f} | T1:{t1_l:.2f} | T2:{t2_l:.2f} | "
                f"Fib1618:{fib_l_1618:.2f} | Score:{score_l:.1f}/10 | "
                f"[Gma:{gma_l} Mo:{mo_l} Ichi:{ichi_l} BOS:{bos_l_pts} "
                f"Zone:{zone_l} EMA:{ema_l} Mom:{mom_l} Liq:{liq_l} "
                f"Trig:{trig_l} Bon:{bon_l}] | WillR:{wr:.1f}")

        # ── SHORT ENTRY ────────────────────────────────────────────────────
        if (short_signal and not self._S_active and not self._L_active and
            not full_exit_s and short_mult>0):

            dist_sz = max(stop_s-close, 0.5*atr)
            qty_short = _lots_to_buy(dist_sz, short_mult, is_short=True)

            # T2 target (below entry)
            t2_s_cands = [fib_s_1272]
            if ssl_lvl and ssl_lvl<t1_s: t2_s_cands.append(ssl_lvl)
            for z in self._demand_zones:
                if z.active and z.top<t1_s: t2_s_cands.append(z.top)
            t2_s = max(t2_s_cands)

            self._S_active=True; self._S_entry_stop=stop_s
            self._S_t1=t1_s; self._S_t2=t2_s
            self._S_t1_done=False; self._S_t2_done=False
            self._S_trail_low=None; self._S_bars=0
            self._S_entry_type=short_type; self._S_lots=qty_short//self._lot

            self.market_order(self._sym, -qty_short, tag=f"S_Entry_{short_type}")
            self.log(
                f"SHORT {short_type} | {t.date()} | "
                f"Price:{close:.2f} | Qty:{qty_short}({self._S_lots}lots) | "
                f"Stop:{stop_s:.2f} | T1:{t1_s:.2f} | T2:{t2_s:.2f} | "
                f"Fib1618:{fib_s_1618:.2f} | Score:{score_s:.1f}/10 | "
                f"[Gma:{gma_s} Mo:{mo_s} Ichi:{ichi_s} BOS:{bos_s_pts} "
                f"Zone:{zone_s} EMA:{ema_s} Mom:{mom_s} Liq:{liq_s} "
                f"Trig:{trig_s} Bon:{bon_s}] | WillR:{wr:.1f}")

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _pivot(self, bars, length):
        if len(bars) < 2*length+1: return None, None
        c=bars[length]
        ph=(c.high if (all(c.high>=bars[i].high for i in range(length)) and
                       all(c.high>=bars[length+j+1].high for j in range(length)))
             else None)
        pl=(c.low  if (all(c.low<=bars[i].low  for i in range(length)) and
                       all(c.low<=bars[length+j+1].low  for j in range(length)))
             else None)
        return ph, pl

    def _upd_bsl(self, ph, idx, mg):
        count=sum(1 for p,_ in self._piv_highs if abs(p-ph)<=mg)
        if count>=3:
            lvl=sum(p for p,_ in self._piv_highs if abs(p-ph)<=mg)/count
            if not any(abs(z.level-lvl)<mg for z in self._bsl_zones):
                fb=min((i for p,i in self._piv_highs if abs(p-ph)<=mg),default=idx)
                self._bsl_zones.appendleft(LiqZ(lvl,True,fb,False))

    def _upd_ssl(self, pl, idx, mg):
        count=sum(1 for p,_ in self._piv_lows if abs(p-pl)<=mg)
        if count>=3:
            lvl=sum(p for p,_ in self._piv_lows if abs(p-pl)<=mg)/count
            if not any(abs(z.level-lvl)<mg for z in self._ssl_zones):
                fb=min((i for p,i in self._piv_lows if abs(p-pl)<=mg),default=idx)
                self._ssl_zones.appendleft(LiqZ(lvl,False,fb,False))

    def _reset_long(self):
        self._L_active=False; self._L_entry_stop=None
        self._L_t1=None; self._L_t2=None
        self._L_t1_done=False; self._L_t2_done=False
        self._L_trail_high=None; self._L_bars=0
        self._L_entry_type=None; self._L_lots=0
        self._spider_bo_occ=False; self._spider_rt_seen=False

    def _reset_short(self):
        self._S_active=False; self._S_entry_stop=None
        self._S_t1=None; self._S_t2=None
        self._S_t1_done=False; self._S_t2_done=False
        self._S_trail_low=None; self._S_bars=0
        self._S_entry_type=None; self._S_lots=0

    def on_order_event(self, order_event):
        if order_event.status==OrderStatus.FILLED:
            self.log(f"FILL | {order_event.symbol} | "
                     f"{order_event.fill_quantity:+.0f} | "
                     f"@{order_event.fill_price:.2f} | "
                     f"{order_event.ticket.tag}")

    def on_end_of_algorithm(self):
        pv=self.portfolio.total_portfolio_value
        pnl=pv-self.starting_portfolio_value
        self.log("═"*70)
        self.log("NEXUS F&O STRATEGY — FINAL SUMMARY")
        self.log("═"*70)
        self.log(f"  Symbol : {self._sym} | Lot size: {self._lot}")
        self.log(f"  Start  : {self.starting_portfolio_value:>12,.2f}")
        self.log(f"  Final  : {pv:>12,.2f}")
        self.log(f"  P&L    : {pnl:>+12,.2f}  ({pnl/self.starting_portfolio_value*100:+.2f}%)")
        self.log(f"  Trades : {self.trade_builder.closed_trade_count}")
        self.log("═"*70)
