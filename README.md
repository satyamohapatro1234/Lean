# 🌍 Global AI Trading Platform

> Open-source, AI-native algorithmic trading terminal built on QuantConnect LEAN.  
> Works with any broker worldwide. Runs offline. No cloud dependency.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![LEAN](https://img.shields.io/badge/Engine-QuantConnect%20LEAN-orange.svg)](https://github.com/QuantConnect/Lean)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Phase%200%20(Foundation)-yellow.svg)](PLAN.md)

---

## 📋 Read the Full Plan

**→ [PLAN.md](PLAN.md)** — Complete architecture, all 8 phases, agent design, AlgoLoop analysis, book-based corrections

---

## 🔬 Research Summary

| Finding | Detail |
|---------|--------|
| LEAN + Agents | ✅ Proven by [quantconnect-mcp](https://github.com/taylorwilsdon/quantconnect-mcp) (85 stars) |
| AlgoLoop frontend | ❌ C# WPF Windows-only — cannot use directly |
| AlgoLoop patterns | ✅ Architecture + LEAN communication pattern extracted |
| First broker | Dhan (provides historical options + OI data) |
| AI framework | LangGraph (stateful agents, human-in-the-loop, Ollama compatible) |

---

## 🏗️ Architecture

```
9 AI Agents (LangGraph) ──► Local LEAN Engine ──► Dhan → Zerodha → IB → ...
        │                         │
        └──────────────► FastAPI ─┘
                              │
                    React Frontend (Next.js)
                    TradingView Charts
                    Option Chain + Strategy Builder
```

---

## 🚦 Development Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0 | 🟡 In Progress | Foundation: instrument master, symbol mapper, data pipeline, first backtest |
| Phase 1 | ⚪ Planned | Strategy validation (Walk Forward + Monte Carlo) |
| Phase 2 | ⚪ Planned | Dhan live integration + paper trading |
| Phase 3 | ⚪ Planned | Core agents (BacktestOrchestrator, RiskMonitor, MCP) |
| Phase 4 | ⚪ Planned | Options intelligence + 2 more agents |
| Phase 5 | ⚪ Planned | More Indian brokers (Zerodha, Upstox, Angel, Fyers) |
| Phase 6 | ⚪ Planned | Global markets (Interactive Brokers) |
| Phase 7 | ⚪ Planned | Full React trading terminal |
| Phase 8 | ⚪ Planned | Open source launch |

---

## 🤖 9 AI Agents

| Agent | Phase | Role |
|-------|-------|------|
| BacktestOrchestrator | 3 | Natural language → runs backtests |
| RiskMonitor | 3 | Watches positions, fires alerts |
| OptimizerAgent | 3 | Grid/Euler parameter search |
| WaveSignal | 4 | Spider MTF Wave System signals |
| StrategyAdvisor | 4 | Market view → options structure |
| NewsAnalyst | 5 | Sentiment → market impact |
| OrderAssist | 5 | Natural language → orders |
| MarketScan | 5 | Global OI/IV/unusual activity |
| PortfolioCoach | 5 | Daily P&L + position sizing |

---

*See [PLAN.md](PLAN.md) for full technical details, book-based analysis, and AlgoLoop findings.*
