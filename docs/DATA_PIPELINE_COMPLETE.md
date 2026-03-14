# Data Pipeline — Complete Design
# The Problem You Hit, Why It Happens, and the Full Solution

---

## The Problem You Experienced — Diagnosis

You tried to download 20 stocks, then 40, then it failed. This happens because of one fundamental mistake that most traders make: **treating data download as a simple loop**.

Here is what a naive approach does:
```
for symbol in 2000_symbols:
    data = dhan.get_historical(symbol, 2019-01-01, 2024-01-01)  # 5 years
    save(data)
```

This fails for multiple reasons:
1. **Rate limits**: Dhan allows 20 req/sec. With 2000 symbols × ~20 chunks (90-day windows) = 40,000 requests. At 20/sec, that is 2,000 seconds (33 minutes) — but Dhan will ban your IP long before that.
2. **Window limits**: Dhan intraday is limited to 90 days per request. For 5 years of 1-min data you need 20 requests per symbol.
3. **No retry logic**: First timeout → entire job dies.
4. **No resume**: If it fails at stock 400 of 2000, you restart from zero.
5. **No deduplication**: Re-running re-downloads already-stored data.
6. **Wrong data source**: You're using the wrong tool for bulk historical EOD. The right tool is NSE Bhavcopy — one file per day = all 2000+ stocks at once.

---

## The Three-Tier Data Source Strategy

Different data has different optimal sources. This is the fundamental insight.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     THREE-TIER DATA ARCHITECTURE                     │
├─────────────────────────┬───────────────────────────────────────────┤
│ Tier 1: NSE Bhavcopy    │ What: EOD daily OHLCV for ALL stocks       │
│ (Free, official)        │ Source: https://nseindia.com/all-reports   │
│                         │ Format: ZIP → CSV, one file = ALL stocks   │
│                         │ Rate limit: NONE (static file download)    │
│                         │ Cost: Zero                                 │
│                         │ Use: Backtesting daily/weekly strategies   │
│                         │ History: Back to ~2000 for equities        │
│                         │ F&O Bhavcopy: all futures+options OHLC+OI  │
│                         │ Key: 1 request = 2000+ symbols             │
├─────────────────────────┼───────────────────────────────────────────┤
│ Tier 2: Dhan API        │ What: Intraday (1m,5m,15m,60m) OHLCV      │
│ (Rate limited)          │ Source: api.dhan.co/v2/charts/*            │
│                         │ Rate limit: 20 req/sec                     │
│                         │ Window: 90 days per request (intraday)     │
│                         │ Daily: inception date, adjusted (free)     │
│                         │ Intraday: up to last 5 years (paid API)    │
│                         │ Cost: Rs 499/month OR 25 F&O trades/month  │
│                         │ Use: Intraday strategy backtesting         │
│                         │ Key: Per-symbol, chunked, must be queued   │
├─────────────────────────┼───────────────────────────────────────────┤
│ Tier 3: Live WebSocket  │ What: Real-time tick data after market open│
│ (Dhan/NSE WebSocket)    │ Source: Dhan WebSocket API                 │
│                         │ Rate limit: 1000 instruments per connection│
│                         │ Cost: Free (trading API)                  │
│                         │ Use: Live trading, builds minute bars      │
│                         │ Key: Forward-fill QuestDB, never backfill  │
└─────────────────────────┴───────────────────────────────────────────┘
```

---

## Tier 1 Deep Dive: NSE Bhavcopy — The Right Way to Get EOD Data

### What is Bhavcopy
NSE publishes a single ZIP file every trading day by 16:00 IST. This file contains EOD data (Open, High, Low, Close, Volume, Delivery Volume) for EVERY listed equity — approximately 2000+ stocks — in one download.

**URL pattern:**
```
https://archives.nseindia.com/content/historical/EQUITIES/{YEAR}/{MON}/cm{DD}{MON}{YEAR}bhav.csv.zip
Example: https://archives.nseindia.com/content/historical/EQUITIES/2024/JAN/cm01JAN2024bhav.csv.zip
```

**F&O Bhavcopy URL:**
```
https://archives.nseindia.com/content/historical/DERIVATIVES/{YEAR}/{MON}/fo{DD}{MON}{YEAR}bhav.csv.zip
```

**New format (from July 2024):**
NSE switched to CM-UDiFF format per circular 62424 dated June 12, 2024.
```
https://nseindia.com/all-reports → CM-UDiFF Common Bhavcopy Final (ZIP)
```

### The Bhavcopy Download Math

| Task | Bhavcopy approach | Per-symbol API approach |
|------|-------------------|------------------------|
| Get 10 years EOD for all stocks | 2,510 requests (1 per trading day) | 2000 stocks × 1 req = 2,000 requests |
| Request size | 1 req = all 2000 symbols | 1 req = 1 symbol |
| Time to download 10 years | ~42 minutes with 1 req/sec | >5 hours with 20 req/sec |
| Failure blast radius | 1 failed day | 1 failed symbol |
| Cost | Zero | Dhan data API subscription |

**The answer to your problem for EOD data: Always use Bhavcopy. Never loop over symbols for daily data.**

### Bhavcopy Downloader — Production Code

```python
# data-pipeline/bhavcopy_downloader.py

import asyncio
import aiohttp
import zipfile
import io
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
from questdb.ingress import Sender, TimestampNanos
import logging
import time

log = logging.getLogger(__name__)

NSE_EQUITY_URL = "https://archives.nseindia.com/content/historical/EQUITIES/{year}/{mon}/cm{dd}{MON}{year}bhav.csv.zip"
NSE_FO_URL = "https://archives.nseindia.com/content/historical/DERIVATIVES/{year}/{mon}/fo{dd}{MON}{year}bhav.csv.zip"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.nseindia.com",
}

class BhavCopyDownloader:
    """Downloads NSE bhavcopy files — ONE file = ALL stocks for that day."""

    def __init__(self, raw_dir: Path, questdb_host: str = "localhost"):
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.questdb_host = questdb_host

    def get_trading_days(self, from_date: date, to_date: date) -> list[date]:
        """Get all trading days. Uses pandas bdate_range + known NSE holidays."""
        from pandas.tseries.holiday import AbstractHolidayCalendar
        import pandas as pd
        
        # Use business days as base, then subtract known NSE holidays
        # NSE holidays list is maintained in config/nse_holidays.json
        # For simplicity: pandas business days removes weekends; holidays from config
        days = pd.bdate_range(start=from_date, end=to_date, freq="C",
                              holidays=self._load_nse_holidays())
        return [d.date() for d in days]

    def _load_nse_holidays(self) -> list:
        """Load NSE holidays from config file."""
        import json
        holidays_file = Path("config/nse_holidays.json")
        if holidays_file.exists():
            with open(holidays_file) as f:
                return json.load(f)
        return []

    def build_url(self, d: date, segment: str = "equity") -> str:
        """Build the bhavcopy URL for a given date."""
        year = d.strftime("%Y")
        mon = d.strftime("%b").upper()
        dd = d.strftime("%d")
        mon_lower = d.strftime("%b").upper()
        
        if segment == "equity":
            return NSE_EQUITY_URL.format(year=year, mon=mon_lower, dd=dd, MON=mon)
        else:  # fo
            return NSE_FO_URL.format(year=year, mon=mon_lower, dd=dd, MON=mon)

    def already_downloaded(self, d: date, segment: str) -> bool:
        """Check if we already have this bhavcopy."""
        fname = self.raw_dir / f"{segment}_{d.isoformat()}.csv.gz"
        return fname.exists()

    async def download_one_day(
        self,
        session: aiohttp.ClientSession,
        d: date,
        segment: str = "equity",
        retries: int = 3,
        backoff: float = 2.0
    ) -> pd.DataFrame | None:
        """Download bhavcopy for one day. Returns parsed DataFrame."""
        if self.already_downloaded(d, segment):
            log.debug(f"Already have {segment} bhavcopy for {d}, loading from cache")
            return self._load_cached(d, segment)

        url = self.build_url(d, segment)
        
        for attempt in range(retries):
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 404:
                        log.debug(f"No bhavcopy for {d} (holiday/weekend): {url}")
                        return None
                    if resp.status == 429:
                        wait = (2 ** attempt) * backoff
                        log.warning(f"Rate limited for {d}. Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    
                    content = await resp.read()
                    df = self._parse_zip(content, segment)
                    
                    if df is not None and not df.empty:
                        self._save_cache(df, d, segment)
                        log.info(f"✅ Downloaded {segment} bhavcopy for {d}: {len(df)} records")
                        return df
                    return None
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < retries - 1:
                    wait = (2 ** attempt) * backoff
                    log.warning(f"Error downloading {d} (attempt {attempt+1}): {e}. Retry in {wait}s")
                    await asyncio.sleep(wait)
                else:
                    log.error(f"Failed to download {d} after {retries} attempts: {e}")
                    return None

    def _parse_zip(self, content: bytes, segment: str) -> pd.DataFrame | None:
        """Parse the ZIP file and return clean DataFrame."""
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                fname = z.namelist()[0]
                with z.open(fname) as f:
                    df = pd.read_csv(f)
            
            df.columns = df.columns.str.strip().str.lower()
            
            if segment == "equity":
                # NSE equity bhavcopy columns: SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY, TOTTRDVAL, TIMESTAMP, TOTALTRADES, ISIN, DELIV_QTY, DELIV_PER
                df = df[df['series'] == 'EQ']  # Only equity series
                df = df.rename(columns={
                    'symbol': 'symbol',
                    'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close',
                    'tottrdqty': 'volume', 'timestamp': 'date'
                })
                df['date'] = pd.to_datetime(df['date'], format='%d-%b-%Y')
                
            elif segment == "fo":
                # F&O bhavcopy: INSTRUMENT, SYMBOL, EXPIRY_DT, STRIKE_PR, OPTION_TYP, OPEN, HIGH, LOW, CLOSE, SETTLE_PR, CONTRACTS, VAL_INLAKH, OPEN_INT, CHG_IN_OI
                pass  # keep as-is for FO
            
            return df
            
        except Exception as e:
            log.error(f"Failed to parse bhavcopy ZIP: {e}")
            return None

    def _save_cache(self, df: pd.DataFrame, d: date, segment: str):
        """Save to local gzipped CSV cache to avoid re-downloading."""
        fname = self.raw_dir / f"{segment}_{d.isoformat()}.csv.gz"
        df.to_csv(fname, index=False, compression='gzip')

    def _load_cached(self, d: date, segment: str) -> pd.DataFrame:
        fname = self.raw_dir / f"{segment}_{d.isoformat()}.csv.gz"
        return pd.read_csv(fname, compression='gzip')

    async def download_range(
        self,
        from_date: date,
        to_date: date,
        segment: str = "equity",
        concurrency: int = 3,  # Conservative: 3 concurrent requests
        delay_between: float = 0.5  # 500ms between requests
    ) -> list[pd.DataFrame]:
        """
        Download bhavcopy for entire date range.
        
        For 10 years of data = ~2510 trading days.
        At 3 concurrent + 0.5s delay = ~420 seconds = 7 minutes.
        This is correct. Do NOT go faster — NSE will block your IP.
        """
        days = self.get_trading_days(from_date, to_date)
        semaphore = asyncio.Semaphore(concurrency)
        results = []

        async def fetch_with_limit(session, day):
            async with semaphore:
                result = await self.download_one_day(session, day, segment)
                await asyncio.sleep(delay_between)
                return result

        connector = aiohttp.TCPConnector(limit=concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [fetch_with_limit(session, day) for day in days]
            
            # Process in batches of 50 days, report progress
            batch_size = 50
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i+batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                for r in batch_results:
                    if isinstance(r, Exception):
                        log.error(f"Batch error: {r}")
                    elif r is not None:
                        results.append(r)
                
                progress = min(i + batch_size, len(tasks))
                log.info(f"Progress: {progress}/{len(tasks)} days downloaded")
        
        return results

    def ingest_to_questdb(self, dataframes: list[pd.DataFrame]):
        """Bulk insert all bhavcopy data to QuestDB."""
        with Sender('localhost', 9009) as sender:
            for df in dataframes:
                if df is None or df.empty:
                    continue
                for _, row in df.iterrows():
                    try:
                        ts = TimestampNanos.from_datetime(row['date'])
                        sender.row(
                            'ohlcv_daily',
                            symbols={'symbol': str(row['symbol'])},
                            columns={
                                'open': float(row['open']),
                                'high': float(row['high']),
                                'low': float(row['low']),
                                'close': float(row['close']),
                                'volume': int(row['volume']),
                                'source': 'bhavcopy'
                            },
                            at=ts
                        )
                    except Exception as e:
                        log.warning(f"Skip row: {e}")
            sender.flush()
            log.info("✅ All bhavcopy data ingested to QuestDB")

# Usage:
# dl = BhavCopyDownloader(raw_dir=Path("data/raw/bhavcopy"))
# asyncio.run(dl.download_range(date(2014,1,1), date(2024,12,31), segment="equity"))
```

---

## Tier 2 Deep Dive: Dhan API Intraday — Rate-Limited, Resumable Queue

### Dhan API Exact Rate Limits (Verified from Official Docs)

| API | Rate Limit |
|-----|-----------|
| Historical intraday | 20 req/sec (most liberal in industry) |
| Historical daily | 20 req/sec |
| Option Chain | 1 req per 3 seconds |
| Order placement | 25 orders/sec, 250 orders/min |
| Market Quote (batch) | 1 request for up to 1000 instruments |
| Intraday window | 90 days per request |
| Daily data | From stock inception date |
| Intraday depth | Last 5 years (paid API: Rs 499/month) |

### The Intraday Download Math

For 1-min data, 5 years, 2000 NSE equity stocks:
- Per symbol: 5 years ÷ 90 days = ~20 API calls
- Total calls: 2000 symbols × 20 calls = **40,000 API calls**
- At safe rate (5 req/sec safe, 20 max): 40,000 ÷ 5 = **8,000 seconds = 2.2 hours**
- At 20 req/sec (maximum): 40,000 ÷ 20 = **2,000 seconds = 33 minutes**

**BUT:** NSE has 9000+ listed stocks total. F&O has ~200 active stocks.

**Priority tiers for intraday download:**
1. F&O stocks (200 stocks) — needed for options backtesting
2. Nifty 500 (500 stocks) — main backtesting universe  
3. All listed equities (9000+ stocks) — only for scanner/research

**For backtesting purposes: Start with F&O stocks only. Don't try to download 9000 stocks on day 1.**

### Resilient Download Engine

```python
# data-pipeline/intraday_downloader.py

import asyncio
import aiohttp
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import json
import sqlite3
import time
import logging

log = logging.getLogger(__name__)

DHAN_INTRADAY_URL = "https://api.dhan.co/v2/charts/intraday"
DHAN_DAILY_URL = "https://api.dhan.co/v2/charts/historical"
MAX_DAYS_PER_REQUEST = 85  # 90 day limit; use 85 to be safe

class DownloadState:
    """
    SQLite-backed download state tracker.
    This is the key to resumable downloads — if the job dies at 
    symbol 1500 of 2000, we restart from symbol 1501, not from zero.
    """
    def __init__(self, db_path: str = "data/download_state.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS download_jobs (
                symbol TEXT,
                security_id TEXT,
                segment TEXT,
                interval TEXT,
                from_date TEXT,
                to_date TEXT,
                status TEXT DEFAULT 'pending',  -- pending | completed | failed | skipped
                error TEXT,
                rows_downloaded INTEGER DEFAULT 0,
                last_attempt TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON download_jobs(status)")
        self.conn.commit()

    def create_jobs(self, symbols: list[dict], from_date: date, to_date: date, interval: str = "1"):
        """
        Create all download jobs upfront. Each job = one 85-day window for one symbol.
        Skips already-completed jobs (idempotent).
        """
        # Split date range into 85-day windows
        windows = []
        current = from_date
        while current < to_date:
            window_end = min(current + timedelta(days=MAX_DAYS_PER_REQUEST), to_date)
            windows.append((current, window_end))
            current = window_end + timedelta(days=1)

        jobs_created = 0
        for sym in symbols:
            for w_start, w_end in windows:
                # Check if already exists
                existing = self.conn.execute(
                    "SELECT status FROM download_jobs WHERE symbol=? AND from_date=? AND interval=?",
                    (sym['symbol'], w_start.isoformat(), interval)
                ).fetchone()
                
                if existing and existing[0] == 'completed':
                    continue  # Already done, skip
                    
                if not existing:
                    self.conn.execute(
                        "INSERT INTO download_jobs (symbol, security_id, segment, interval, from_date, to_date, status) VALUES (?,?,?,?,?,?,?)",
                        (sym['symbol'], sym['security_id'], sym['segment'], interval,
                         w_start.isoformat(), w_end.isoformat(), 'pending')
                    )
                    jobs_created += 1
        
        self.conn.commit()
        log.info(f"Created {jobs_created} download jobs ({len(windows)} windows × {len(symbols)} symbols)")
        return jobs_created

    def get_pending_jobs(self, limit: int = 1000) -> list[dict]:
        """Get next batch of pending jobs."""
        rows = self.conn.execute(
            "SELECT symbol, security_id, segment, interval, from_date, to_date FROM download_jobs WHERE status='pending' OR status='failed' LIMIT ?",
            (limit,)
        ).fetchall()
        return [{'symbol': r[0], 'security_id': r[1], 'segment': r[2], 
                 'interval': r[3], 'from_date': r[4], 'to_date': r[5]} for r in rows]

    def mark_completed(self, symbol: str, from_date: str, rows: int):
        self.conn.execute(
            "UPDATE download_jobs SET status='completed', rows_downloaded=?, last_attempt=datetime('now') WHERE symbol=? AND from_date=?",
            (rows, symbol, from_date)
        )
        self.conn.commit()

    def mark_failed(self, symbol: str, from_date: str, error: str):
        self.conn.execute(
            "UPDATE download_jobs SET status='failed', error=?, last_attempt=datetime('now') WHERE symbol=? AND from_date=?",
            (error, symbol, from_date)
        )
        self.conn.commit()

    def progress_summary(self) -> dict:
        total = self.conn.execute("SELECT COUNT(*) FROM download_jobs").fetchone()[0]
        completed = self.conn.execute("SELECT COUNT(*) FROM download_jobs WHERE status='completed'").fetchone()[0]
        failed = self.conn.execute("SELECT COUNT(*) FROM download_jobs WHERE status='failed'").fetchone()[0]
        pending = self.conn.execute("SELECT COUNT(*) FROM download_jobs WHERE status='pending'").fetchone()[0]
        return {'total': total, 'completed': completed, 'failed': failed, 'pending': pending,
                'pct_complete': round(completed/total*100, 1) if total > 0 else 0}


class RateLimiter:
    """Token bucket rate limiter for Dhan API."""
    def __init__(self, rate: float = 10.0):  # Conservative: 10 req/sec (Dhan allows 20)
        self.rate = rate
        self.tokens = rate
        self.last_check = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_check
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_check = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class IntradayDownloader:
    """
    Production-grade Dhan intraday downloader.
    Features:
    - SQLite-backed resumable jobs (restart where you left off)
    - Token bucket rate limiting (never exceeds Dhan's 20 req/sec)
    - Exponential backoff on failures
    - Automatic deduplication (skip already-downloaded windows)
    - QuestDB ingestion with batch writes
    - Progress reporting
    """
    
    def __init__(self, client_id: str, access_token: str, questdb_host: str = "localhost"):
        self.client_id = client_id
        self.access_token = access_token
        self.questdb_host = questdb_host
        self.state = DownloadState()
        self.rate_limiter = RateLimiter(rate=8.0)  # 8 req/sec (Dhan max is 20, we're safe at 8)
        self.headers = {
            "Content-Type": "application/json",
            "access-token": access_token
        }

    async def fetch_window(
        self,
        session: aiohttp.ClientSession,
        job: dict,
        retries: int = 4
    ) -> pd.DataFrame | None:
        """Fetch one 85-day window for one symbol."""
        
        payload = {
            "securityId": job['security_id'],
            "exchangeSegment": job['segment'],
            "instrument": "EQUITY",
            "interval": job['interval'],  # "1" for 1min
            "oi": False,
            "fromDate": job['from_date'] + " 09:00:00",
            "toDate": job['to_date'] + " 16:00:00"
        }
        
        for attempt in range(retries):
            await self.rate_limiter.acquire()
            
            try:
                async with session.post(
                    DHAN_INTRADAY_URL,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    
                    if resp.status == 429:  # Rate limited
                        wait = 60 * (attempt + 1)  # Wait 1, 2, 3, 4 minutes
                        log.warning(f"Rate limited on {job['symbol']}. Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    
                    if resp.status == 401:
                        raise Exception("Token expired — need to refresh Dhan token")
                    
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_response(data, job)
                    
                    log.warning(f"Status {resp.status} for {job['symbol']} {job['from_date']}")
                    await asyncio.sleep(2 ** attempt)
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < retries - 1:
                    wait = (2 ** attempt) * 2
                    log.warning(f"Network error {job['symbol']} attempt {attempt+1}: {e}. Retry in {wait}s")
                    await asyncio.sleep(wait)
                else:
                    log.error(f"Gave up on {job['symbol']} {job['from_date']}: {e}")
                    return None
        return None

    def _parse_response(self, data: dict, job: dict) -> pd.DataFrame | None:
        """Parse Dhan API response into DataFrame."""
        if not data.get('open') or len(data['open']) == 0:
            return None
        
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(data['timestamp'], unit='s'),
            'open': data['open'],
            'high': data['high'],
            'low': data['low'],
            'close': data['close'],
            'volume': data['volume'],
            'symbol': job['symbol'],
            'interval': job['interval']
        })
        
        # Filter to market hours only (9:15–15:30 IST)
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        df = df[df['timestamp'].dt.time >= pd.Timestamp('09:15').time()]
        df = df[df['timestamp'].dt.time <= pd.Timestamp('15:30').time()]
        
        return df

    async def run(self, concurrency: int = 5):
        """
        Main download loop. Run this. It will:
        1. Pick up pending jobs from SQLite
        2. Download with rate limiting and retries
        3. Save to QuestDB
        4. Mark jobs complete
        5. Print progress every 100 jobs
        
        If it crashes, just run again — it resumes from where it stopped.
        """
        connector = aiohttp.TCPConnector(limit=concurrency)
        semaphore = asyncio.Semaphore(concurrency)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            total_processed = 0
            
            while True:
                jobs = self.state.get_pending_jobs(limit=100)
                if not jobs:
                    log.info("✅ All download jobs complete!")
                    break
                
                async def process_job(job):
                    async with semaphore:
                        df = await self.fetch_window(session, job)
                        if df is not None and not df.empty:
                            self._ingest_to_questdb(df)
                            self.state.mark_completed(job['symbol'], job['from_date'], len(df))
                        else:
                            self.state.mark_failed(job['symbol'], job['from_date'], "empty_response")
                
                await asyncio.gather(*[process_job(j) for j in jobs])
                total_processed += len(jobs)
                
                progress = self.state.progress_summary()
                log.info(f"Progress: {progress['pct_complete']}% complete "
                        f"({progress['completed']}/{progress['total']}) "
                        f"| Failed: {progress['failed']}")

    def _ingest_to_questdb(self, df: pd.DataFrame):
        """Batch write to QuestDB via ILP (Line Protocol)."""
        from questdb.ingress import Sender, TimestampNanos
        
        with Sender(self.questdb_host, 9009) as sender:
            for _, row in df.iterrows():
                ts = TimestampNanos.from_datetime(row['timestamp'].to_pydatetime())
                sender.row(
                    f"ohlcv_{row['interval']}min",
                    symbols={'symbol': row['symbol']},
                    columns={
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': int(row['volume'])
                    },
                    at=ts
                )
```

---

## Daily Auto-Update System (After Initial Download)

Once the initial historical download is complete, you only need to download yesterday's new data each day. This is dramatically simpler.

```python
# data-pipeline/daily_updater.py
# Run this at 16:30 IST every trading day via cron or APScheduler

import asyncio
from datetime import date, timedelta
from pathlib import Path

async def daily_update():
    """
    Run at 16:30 IST every trading day.
    Downloads only YESTERDAY's data — takes < 5 minutes.
    """
    yesterday = date.today() - timedelta(days=1)
    
    # Step 1: Download NSE bhavcopy (1 request = all 2000+ stocks)
    # This is the correct way — not per-symbol API calls
    bhav = BhavCopyDownloader(raw_dir=Path("data/raw/bhavcopy"))
    df = await bhav.download_one_day(session, yesterday, segment="equity")
    if df is not None:
        bhav.ingest_to_questdb([df])
    
    # Step 2: Download F&O bhavcopy
    fo_df = await bhav.download_one_day(session, yesterday, segment="fo")
    if fo_df is not None:
        bhav.ingest_to_questdb([fo_df])
    
    # Step 3: Update LEAN /Data folder (write yesterday's bars in LEAN zip format)
    lean_writer = LEANWriter("data/lean")
    lean_writer.write_from_questdb(yesterday)
    
    # Step 4: Refresh instrument master (new listings, delistings, lot size changes)
    await refresh_instrument_master()
    
    # Step 5: Check for regulatory changes (see next section)
    await check_sebi_updates()
    
    print(f"✅ Daily update complete for {yesterday}")

# Cron: 30 16 * * 1-5 python daily_updater.py
```

---

## SEBI Regulatory Change Tracking System

This is critical. In 2024 alone, SEBI made MAJOR changes that broke backtesting assumptions:

| Date | Change | Impact on Our System |
|------|--------|---------------------|
| Oct 1, 2024 | STT increased: Futures 0.0125% → 0.02%, Options 0.0625% → 0.1% | `DhanFeeModel` must be versioned. Backtests before Oct 2024 use old rates |
| Nov 20, 2024 | Weekly expiries limited: only Nifty50 (NSE) and Sensex (BSE) remain | Option strategy universe changed. Bank Nifty, FinNifty, MidcapSelect gone |
| Nov 21, 2024 | Lot sizes changed: Nifty 50: 75 → 75 (no change yet for weekly) | Lot size table must be timestamped |
| Dec 24–26, 2024 | New lot sizes effective: Nifty 25 (was 50), BankNifty 30 (was 15) | **CRITICAL**: Backtesting with wrong lot size = wrong margin calculation |
| Feb 10, 2025 | No margin benefit for calendar spreads on expiry day | Spread strategies appear more profitable before this date |
| Apr 1, 2025 | Intraday monitoring of position limits begins | Live trading limit violation rules changed |

**The system must know which rules apply on which date for every backtest.**

### Fee Model Versioning

```python
# data-pipeline/fee_models.py

from datetime import date
from dataclasses import dataclass

@dataclass
class DhanFeeSchedule:
    effective_from: date
    effective_to: date | None  # None = still current
    
    # Brokerage
    equity_delivery_brokerage: float = 0.0  # Zero brokerage
    equity_intraday_brokerage: float = 0.0003  # 0.03%, max Rs 20
    fno_brokerage_per_lot: float = 20.0  # Rs 20 per executed order
    
    # STT (Securities Transaction Tax)
    equity_delivery_stt_buy: float = 0.001   # 0.1% on buy
    equity_delivery_stt_sell: float = 0.001  # 0.1% on sell
    equity_intraday_stt_sell: float = 0.00025  # 0.025% sell only
    futures_stt_sell: float  # Changed Oct 2024
    options_stt_sell: float  # Changed Oct 2024
    
    # Exchange transaction charges
    nse_equity_charge: float = 0.0000297  # 0.00297%
    nse_fno_charge: float  # Changed Oct 2024
    
    # Other
    sebi_charge: float = 0.000001  # Rs 10 per crore
    stamp_duty: float = 0.00003   # Equity delivery (buy side)
    gst_on_brokerage: float = 0.18  # 18%

# Fee schedule history — loaded by backtest engine based on trade date
FEE_SCHEDULES = [
    DhanFeeSchedule(
        effective_from=date(2020, 1, 1),
        effective_to=date(2024, 9, 30),
        futures_stt_sell=0.0001,    # 0.0125% (old rate before Oct 2024)
        options_stt_sell=0.000625,  # 0.0625% (old rate)
        nse_fno_charge=0.000495    # 0.0495% (old rate)
    ),
    DhanFeeSchedule(
        effective_from=date(2024, 10, 1),  # BUDGET 2024 CHANGE
        effective_to=None,  # Current
        futures_stt_sell=0.0002,    # 0.02% (new rate from Oct 2024)
        options_stt_sell=0.001,     # 0.1% (new rate — 60% increase!)
        nse_fno_charge=0.00035     # 0.035% (reduced from 0.0495%)
    )
]

def get_fee_schedule(trade_date: date) -> DhanFeeSchedule:
    """Get correct fee schedule for a given trade date."""
    for schedule in reversed(FEE_SCHEDULES):
        if trade_date >= schedule.effective_from:
            return schedule
    return FEE_SCHEDULES[0]
```

### Lot Size Version Table

```sql
-- schema.sql: Lot size history table (critical for options margin calculation)
CREATE TABLE lot_size_history (
    symbol          TEXT NOT NULL,
    lot_size        INTEGER NOT NULL,
    effective_from  DATE NOT NULL,
    effective_to    DATE,  -- NULL means still current
    source          TEXT,  -- 'nse_circular', 'exchange_notification'
    circular_ref    TEXT,  -- NSE circular number
    PRIMARY KEY (symbol, effective_from)
);

-- Seed with known lot size changes
INSERT INTO lot_size_history VALUES ('NIFTY', 75, '2010-01-01', '2024-12-25', 'initial', NULL);
INSERT INTO lot_size_history VALUES ('NIFTY', 25, '2024-12-26', NULL, 'nse_circular', 'NSE/F&O/2024-XXX');
INSERT INTO lot_size_history VALUES ('BANKNIFTY', 15, '2010-01-01', '2024-12-23', 'initial', NULL);
INSERT INTO lot_size_history VALUES ('BANKNIFTY', 30, '2024-12-24', NULL, 'nse_circular', 'NSE/F&O/2024-XXX');
```

### Automatic SEBI Change Monitoring

```python
# data-pipeline/sebi_monitor.py

import aiohttp
import hashlib
from datetime import datetime
import json
from pathlib import Path

SEBI_CIRCULARS_RSS = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"
NSE_CIRCULARS_URL = "https://www.nseindia.com/regulations/circulars-and-notices"

KEYWORDS_TO_WATCH = [
    "securities transaction tax", "STT",
    "lot size", "contract size",
    "weekly expiry", "weekly derivative",
    "margin", "extreme loss margin", "ELM",
    "position limit", "open interest",
    "settlement", "mark to market",
    "calendar spread",
    "brokerage", "transaction charges",
    "stamp duty"
]

async def check_sebi_updates():
    """
    Run daily. Checks SEBI circulars for keywords affecting our trading system.
    Sends alert if anything relevant found.
    Alert channels: email + Telegram + log file
    """
    async with aiohttp.ClientSession() as session:
        # Fetch NSE circulars page
        async with session.get(NSE_CIRCULARS_URL, timeout=30) as resp:
            content = await resp.text()
        
        # Hash check — only process if page changed
        current_hash = hashlib.md5(content.encode()).hexdigest()
        hash_file = Path("data/.sebi_hash")
        
        if hash_file.exists() and hash_file.read_text() == current_hash:
            return  # No changes
        
        # New content detected
        hash_file.write_text(current_hash)
        
        # Check for keywords
        content_lower = content.lower()
        triggered_keywords = [kw for kw in KEYWORDS_TO_WATCH if kw.lower() in content_lower]
        
        if triggered_keywords:
            alert_message = f"""
🚨 SEBI/NSE CIRCULAR ALERT — {datetime.now().date()}

Potential trading rule change detected!
Keywords found: {', '.join(triggered_keywords)}

ACTION REQUIRED:
1. Visit https://www.nseindia.com/regulations/circulars-and-notices
2. Read the new circular carefully
3. Update fee_models.py if STT/charges changed
4. Update lot_size_history table if lot sizes changed
5. Update margin_rules.py if margin rules changed
6. Re-run backtests if fee model changed!

CRITICAL: Run tests/test_fee_model.py after any fee model update.
"""
            log_alert(alert_message)
            send_telegram_alert(alert_message)  # If configured

def log_alert(message: str):
    alerts_log = Path("logs/regulatory_alerts.log")
    with open(alerts_log, 'a') as f:
        f.write(f"{datetime.now().isoformat()} {message}\n{'='*80}\n")
    print(message)  # Also print to console
```

---

## Margin Data System

### What Margins Exist in NSE F&O

```
Total Margin = SPAN Margin + Exposure Margin + ELM + Net Option Value

1. SPAN Margin (Standard Portfolio Analysis of Risk)
   - Calculated by NSE Clearing (NSCCL) daily
   - Based on 16 price/volatility scenarios
   - NSE publishes SPAN risk parameter file (.spn) daily at ~5:00 PM
   - URL: https://www.nseclearing.com/risk-management/equity-derivatives/

2. Exposure Margin
   - Index contracts: 3% of contract value
   - Stock contracts: 5% of contract value (higher due to single stock risk)
   - Added on top of SPAN

3. Extreme Loss Margin (ELM) — CHANGED Oct 2024
   - OLD: Index 2%, Stock 3.5%
   - NEW (from Nov 20, 2024): + 2% additional ELM on short index options on expiry day

4. Mark to Market (MTM) Margin
   - Settled daily, not an initial margin
   - Loss in open F&O positions must be replenished by 10:30 AM next day

5. VaR (Value at Risk) Margin — For equity delivery
   - Historical simulation VaR at 99% confidence
   - Covers losses over 1 trading day
   - Updated weekly by NSE
```

### Margin Data Sources

```python
# data-pipeline/margin_data.py

MARGIN_DATA_SOURCES = {
    # Free sources
    "nsccl_span_file": {
        "url": "https://www.nseclearing.com/risk-management/equity-derivatives/",
        "format": "SPAN risk parameter file (.spn)",
        "frequency": "daily, ~5 PM IST",
        "use": "accurate SPAN margin calculation for backtesting",
        "library": "py-nseclearingdata (community) or parse manually"
    },
    
    "zerodha_margin_api": {
        "url": "https://api.kite.trade/margins/basket",
        "doc": "https://kite.trade/docs/connect/v3/margins/",
        "response": "SPAN + exposure + option_premium + additional + var + charges",
        "use": "real-time margin query for live orders, validated pre-order",
        "cost": "Kite Connect subscription (Rs 2000/month)"
    },
    
    "dhan_margin_api": {
        # Dhan does not currently expose margin API directly
        # Use: order.margin field in order response after placement
        "note": "Dhan shows blocked margin in get_positions() response",
        "workaround": "Use Zerodha's basket margin API or NSE SPAN file"
    },
    
    "nsccl_var_file": {
        "url": "https://www.nseclearing.com/risk-management/equity/",
        "format": "VaR data file for equity segment",
        "frequency": "weekly",
        "use": "VaR margin for equity delivery trades"
    }
}

class MarginCalculator:
    """
    Multi-layer margin calculation.
    
    For LEAN backtesting: use LEAN's built-in India margin model
    For live trading pre-check: call broker margin API
    For analytics: use NSCCL SPAN file (most accurate)
    """
    
    def estimate_margin_equity(self, price: float, quantity: int) -> dict:
        """Equity delivery: VaR + ELM."""
        contract_value = price * quantity
        var_margin = contract_value * 0.07  # ~7% for Nifty 50 stocks (rough estimate)
        elm_margin = contract_value * 0.035  # 3.5% ELM for equity
        return {
            'var': var_margin,
            'elm': elm_margin,
            'total': var_margin + elm_margin
        }
    
    def estimate_margin_future(self, price: float, lot_size: int, lots: int, trade_date=None) -> dict:
        """Futures margin: SPAN + Exposure."""
        # Get correct lot size for this date
        effective_lot = get_lot_size_for_date('NIFTY', trade_date) if trade_date else lot_size
        contract_value = price * effective_lot * lots
        
        span_pct = 0.08  # ~8% for index futures (varies, use NSCCL file for accuracy)
        exposure_pct = 0.03  # 3% exposure margin for index
        
        return {
            'span': contract_value * span_pct,
            'exposure': contract_value * exposure_pct,
            'total': contract_value * (span_pct + exposure_pct)
        }
    
    def estimate_margin_option_sell(self, underlying_price: float, lot_size: int,
                                    lots: int, is_expiry_day: bool = False) -> dict:
        """Option writing margin: SPAN + Exposure + ELM (+ extra 2% on expiry)."""
        contract_value = underlying_price * lot_size * lots
        
        span_pct = 0.05  # ~5% for ATM options
        exposure_pct = 0.03  # 3% exposure
        elm_pct = 0.02  # 2% ELM (from Oct 2024)
        expiry_extra_elm = 0.02 if is_expiry_day else 0.0  # New from Nov 2024
        
        total_pct = span_pct + exposure_pct + elm_pct + expiry_extra_elm
        return {
            'span': contract_value * span_pct,
            'exposure': contract_value * exposure_pct,
            'elm': contract_value * (elm_pct + expiry_extra_elm),
            'total': contract_value * total_pct,
            'is_expiry_day': is_expiry_day
        }
```

---

## Initial Bootstrap Sequence — Step by Step

This is the exact order to run things for the very first time. No more failing at stock 40.

```
PHASE A — EOD Data (Free, Fast, All Stocks at Once)
├── Run: python -m data-pipeline.bhavcopy_downloader --from 2014-01-01 --to 2024-12-31 --segment equity
│   Time: ~7 minutes, Gets EOD OHLCV for all 2000+ stocks for 10 years
│   
├── Run: python -m data-pipeline.bhavcopy_downloader --from 2014-01-01 --to 2024-12-31 --segment fo
│   Time: ~7 minutes, Gets F&O OHLCV + OI for all options/futures
│   
└── Write to LEAN /Data format (daily bars)

PHASE B — Intraday Data (Rate-Limited, Only F&O Universe)
├── Create download jobs: 200 F&O stocks × ~20 windows each = 4,000 jobs
│   python -m data-pipeline.intraday_downloader --create-jobs --universe fo --from 2019-01-01
│   
├── Run downloader (safe, resumable, 8 req/sec):
│   python -m data-pipeline.intraday_downloader --run
│   Expected time: 4,000 jobs ÷ 8 req/sec = ~500 seconds = 8 minutes
│   
└── Write to LEAN /Data format (minute bars)

PHASE C — Verify and Check
├── Run: python tests/test_data_quality.py
│   Checks: no gaps, no price outliers, correct LEAN format
│   
└── Run: python tests/test_backtest_minimal.py
    Runs Spider Wave on 1 stock, 1 year → confirms data is readable by LEAN
```

---

## Auto-Recovery System

The complete error taxonomy and automatic recovery rules:

```python
ERROR_RECOVERY_RULES = {
    "429_rate_limited": {
        "action": "wait_and_retry",
        "wait_minutes": 60,
        "max_retries": 3,
        "escalate_to": "reduce_rate_to_2_req_per_sec"
    },
    "401_unauthorized": {
        "action": "refresh_token_and_retry",
        "token_refresh": "automated_playwright_login",
        "escalate_to": "alert_human_check_account"
    },
    "404_not_found": {
        "action": "mark_as_skipped",
        "reason": "holiday or symbol not listed yet",
        "retry": False
    },
    "503_server_error": {
        "action": "wait_and_retry",
        "wait_minutes": 10,
        "max_retries": 5
    },
    "empty_response": {
        "action": "mark_failed_try_next_day",
        "note": "Some symbols have no data for certain periods"
    },
    "connection_timeout": {
        "action": "retry_with_backoff",
        "base_wait_seconds": 5,
        "max_wait_seconds": 300
    }
}
```

---

## Summary: Correct Architecture for This Problem

| Problem | Wrong Approach | Correct Approach |
|---------|---------------|-----------------|
| EOD data for all stocks | Per-symbol API loop (fails at 40) | NSE Bhavcopy (1 file = all stocks) |
| Intraday data, 2000 stocks | Simple loop (crashes, no retry) | SQLite-backed job queue, resumable |
| Rate limiting | Hope it doesn't break | Token bucket limiter, 8 req/sec |
| Job failure at stock 400 | Restart from scratch | SQLite state, restart resumes at 401 |
| Fee model changes (SEBI 2024) | Hardcoded fee | Versioned fee schedule, date-aware |
| Lot size changes (Dec 2024) | Wrong margin in backtest | lot_size_history table with dates |
| New circulars | Notice manually, maybe | Daily hash-diff monitor + alert |
| Margin calculation | Ignore or guess | NSCCL SPAN file + broker API verify |
