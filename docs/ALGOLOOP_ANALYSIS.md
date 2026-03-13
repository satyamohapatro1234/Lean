# AlgoLoop Analysis — What We Learned and What We Take

**Source:** https://github.com/Capnode/Algoloop  
**Cloned and analyzed:** March 2026

---

## What AlgoLoop Is

Open-source Windows desktop trading application built on top of LEAN.  
Written in C# using WPF (Windows Presentation Foundation).

## Last Commit
July 2025 — still maintained, not abandoned as rumored.

## Technology Stack

| Component | Technology |
|-----------|-----------|
| UI Framework | C# WPF (Windows only) |
| Charts | StockSharp.Xaml.Charting (candlestick) + OxyPlot (equity curve) |
| State Management | MVVM (Model-View-ViewModel) with CommunityToolkit |
| LEAN Connection | Subprocess launch of `QuantConnect.Lean.Launcher.exe` |
| Data format | JSON config files in/out + LEAN zip data files |

## Can We Use It Directly?

**NO.** WPF = Windows-only desktop technology. Cannot run in a browser or on Linux/Mac.

## What We Take From AlgoLoop

### 1. The LEAN Communication Pattern (Most Important)

AlgoLoop's `LeanLauncher.cs` shows exactly how to talk to LEAN from any language:

```python
# AlgoLoop pattern translated to Python (our engine_wrapper.py)
def run_backtest(strategy_name, config_dict):
    tmpdir = tempfile.mkdtemp()
    
    # Step 1: Write config.json
    with open(f"{tmpdir}/config.json", "w") as f:
        json.dump(config_dict, f)
    
    # Step 2: Launch LEAN subprocess
    process = subprocess.Popen(
        ["dotnet", "QuantConnect.Lean.Launcher.dll"],
        cwd=tmpdir
    )
    process.wait()
    
    # Step 3: Read result JSON (AlgoLoop's PostProcess method)
    result_file = f"{tmpdir}/{strategy_name}.json"
    with open(result_file) as f:
        return json.load(f)
```

### 2. The UI Architecture Patterns

AlgoLoop organizes the UI exactly as a professional trading platform should:

```
MarketsViewModel     → our DataProvider page
StrategiesViewModel  → our Strategies panel  
BacktestViewModel    → our BacktestResults with tabs:
  - Configuration tab   (strategy params)
  - Symbols tab         (what instruments traded)
  - Parameters tab      (optimization parameter grid)
  - Holdings tab        (open positions at end)
  - Orders tab          (all orders placed)
  - Trades tab          (executed trades with P&L)
  - Charts tab          (equity curve + custom charts)
```

### 3. The Data Model Structure

AlgoLoop's model classes map directly to what LEAN produces:

```python
# Our Python equivalents of AlgoLoop's C# models
@dataclass
class BacktestResult:
    statistics: dict          # Sharpe, Drawdown, Return etc.
    trades: list[Trade]       # entry/exit with P&L
    orders: list[Order]       # all orders with status
    holdings: list[Holding]   # final positions
    charts: list[Chart]       # equity curve, custom charts

@dataclass  
class Trade:
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: int
    profit_loss: float
    direction: str  # "Long" or "Short"
```

### 4. What's Missing in AlgoLoop (We Build This)

- No Dhan/Zerodha/Upstox/Indian broker support
- No live trading UI (broker config panel is placeholder)
- No real data download (USA provider just downloads QuantConnect sample data)
- No AI agents
- No options chain / strategy builder
- No global markets beyond USA sample data
- Windows-only (cannot run on Linux/Mac/web)

## Summary

AlgoLoop is a valuable reference for:
- How to structure a LEAN-based trading application
- How to communicate with the LEAN engine
- How to organize backtest results in a UI
- What tabs/views a trading platform needs

It is NOT usable directly in our web-based platform.
We build the same architecture in React + FastAPI + Python.
