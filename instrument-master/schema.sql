-- Instrument Master Schema
-- SQLite database: instrument-master/instruments.db
-- Updated: Daily at 6 AM via daily_refresher.py
-- Purpose: Map instrument identifiers across all brokers + LEAN

-- Core instrument table
CREATE TABLE IF NOT EXISTS instruments (
    -- Internal ID
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Exchange identifiers
    isin                TEXT,                          -- Universal ISIN code
    exchange            TEXT NOT NULL,                 -- NSE, BSE, MCX
    segment             TEXT NOT NULL,                 -- EQ, FO, CUR, COM

    -- Common fields
    symbol              TEXT NOT NULL,                 -- Trading symbol (NIFTY, RELIANCE)
    name                TEXT,                          -- Full company name
    instrument_type     TEXT NOT NULL,                 -- EQUITY, FUTURES, OPTIONS, INDEX

    -- Derivative fields (NULL for equity)
    expiry_date         DATE,
    strike_price        REAL,
    option_type         TEXT,                          -- CE or PE
    lot_size            INTEGER,                       -- Current lot size

    -- Broker-specific IDs
    dhan_security_id    TEXT,                          -- Dhan: security_id field
    zerodha_token       TEXT,                          -- Zerodha: instrument_token
    upstox_key          TEXT,                          -- Upstox: instrument_key
    angelone_token      TEXT,                          -- Angel One: token field
    fyers_symbol        TEXT,                          -- Fyers: symbol field

    -- LEAN identifiers
    lean_ticker         TEXT,                          -- LEAN symbol string
    lean_market         TEXT DEFAULT 'India',
    lean_security_type  TEXT,                          -- Equity, Option, Future, Index
    lean_resolution     TEXT DEFAULT 'Minute',

    -- Metadata
    is_active           INTEGER DEFAULT 1,             -- 1=active, 0=delisted
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(exchange, segment, symbol, expiry_date, strike_price, option_type)
);

-- Lot size history (critical for correct margin calculation in backtests)
-- SEBI changed lot sizes Dec 2024: Nifty 50→25, BankNifty 15→30
CREATE TABLE IF NOT EXISTS lot_size_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    lot_size        INTEGER NOT NULL,
    effective_from  DATE NOT NULL,
    effective_to    DATE,                              -- NULL = still current
    source          TEXT,                              -- 'nse_circular', 'sebi_rule'
    circular_ref    TEXT,                              -- NSE circular number if available
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, effective_from)
);

-- Download job queue for Dhan intraday downloader
-- This is how we make bulk downloads resumable (never restart from scratch)
CREATE TABLE IF NOT EXISTS download_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    security_id     TEXT NOT NULL,
    segment         TEXT NOT NULL,
    interval        TEXT NOT NULL,                     -- "1", "5", "15", "60", "D"
    from_date       TEXT NOT NULL,                     -- ISO date string
    to_date         TEXT NOT NULL,
    status          TEXT DEFAULT 'pending',            -- pending|completed|failed|skipped
    error           TEXT,
    rows_downloaded INTEGER DEFAULT 0,
    last_attempt    TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, from_date, interval)
);

-- SEBI regulatory change log
CREATE TABLE IF NOT EXISTS regulatory_changes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    change_date     DATE NOT NULL,
    category        TEXT NOT NULL,                     -- 'stt', 'lot_size', 'margin', 'expiry'
    description     TEXT NOT NULL,
    circular_ref    TEXT,
    impact          TEXT,                              -- How this affects fee model / strategy
    detected_at     TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Seed: Known lot size history
INSERT OR IGNORE INTO lot_size_history (symbol, lot_size, effective_from, effective_to, source)
VALUES
    ('NIFTY',     50, '2010-01-01', '2024-12-25', 'initial'),
    ('NIFTY',     25, '2024-12-26', NULL,          'nse_circular'),
    ('BANKNIFTY', 15, '2010-01-01', '2024-12-23', 'initial'),
    ('BANKNIFTY', 30, '2024-12-24', NULL,          'nse_circular'),
    ('FINNIFTY',  40, '2021-01-01', '2024-11-19', 'initial'),
    ('SENSEX',    10, '2010-01-01', NULL,           'initial'),
    ('BANKEX',    15, '2022-01-01', NULL,           'initial');

-- Seed: Known regulatory changes
INSERT OR IGNORE INTO regulatory_changes (change_date, category, description, impact)
VALUES
    ('2024-10-01', 'stt',      'STT on futures 0.0125%→0.02%, options 0.0625%→0.1%', 'Update fee_schedules.json. Backtests before this date use old rates.'),
    ('2024-11-20', 'expiry',   'Weekly expiries reduced: only Nifty50(NSE) and Sensex(BSE) remain', 'BankNifty, FinNifty, MidcapSelect weekly options removed from strategy universe.'),
    ('2024-12-26', 'lot_size', 'Nifty lot size 50→25, BankNifty 15→30', 'lot_size_history table seeded. Margin calculations use date-aware lookup.'),
    ('2025-02-10', 'margin',   'No calendar spread margin benefit on expiry day', 'Spread strategies appear more profitable before this date in backtests.');

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);
CREATE INDEX IF NOT EXISTS idx_instruments_dhan_id ON instruments(dhan_security_id);
CREATE INDEX IF NOT EXISTS idx_instruments_lean ON instruments(lean_ticker, lean_market);
CREATE INDEX IF NOT EXISTS idx_download_jobs_status ON download_jobs(status);
CREATE INDEX IF NOT EXISTS idx_lot_size_symbol ON lot_size_history(symbol);
