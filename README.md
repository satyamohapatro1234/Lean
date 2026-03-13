# 🌍 Global AI Trading Platform

> Open-source, AI-native algorithmic trading terminal built on QuantConnect LEAN.  
> Works with any broker worldwide. Runs offline. No cloud dependency.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![LEAN](https://img.shields.io/badge/Engine-QuantConnect%20LEAN-orange.svg)](https://github.com/QuantConnect/Lean)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Phase%200%20(Planning)-yellow.svg)](PLAN.md)

---

## 📋 Read the Full Plan First

**→ [PLAN.md](PLAN.md)** — Complete architecture, all phases, agent design, research findings

---

## 🔬 Key Research Finding: LEAN + Agents = YES

Someone already did part of this: [`taylorwilsdon/quantconnect-mcp`](https://github.com/taylorwilsdon/quantconnect-mcp)  
— a production MCP server that lets Claude/GPT control QuantConnect via natural language (85 stars, active).

**We go further:** Local LEAN engine + Indian brokers + offline AI + full trading terminal UI.

---

## 🏗️ What This Builds

```
AI Agents (LangGraph) ──► Local LEAN Engine ──► Any Broker (Zerodha/Upstox/IB/...)
                                │
                    React Frontend (TradingView charts, Option Chain, Strategy Builder)
```

---

## 🚦 Current Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0 | 🟡 In Progress | Foundation: LEAN setup, instrument master, symbol mapper |
| Phase 1 | ⚪ Planned | 5 Indian brokers + IB connected |
| Phase 2 | ⚪ Planned | Backtesting + data pipeline |
| Phase 3 | ⚪ Planned | 8 AI agents (LangGraph) |
| Phase 4 | ⚪ Planned | Options intelligence |
| Phase 5 | ⚪ Planned | Global markets |
| Phase 6 | ⚪ Planned | React trading terminal |

---

## 🤖 8 AI Agents

| Agent | What it Does |
|-------|-------------|
| MarketScan | Scans F&O OI, IV, unusual activity globally |
| StrategyAdvisor | Converts market view → options strategy |
| RiskMonitor | Watches live positions, fires alerts |
| WaveSignal | Spider MTF Wave System signals |
| NewsAnalyst | News sentiment → market impact |
| OrderAssist | Natural language → order placement |
| BacktestOrchestrator | Designs and runs backtests from chat |
| OptimizerAgent | Grid/Euler parameter optimization |

---

*See [PLAN.md](PLAN.md) for full details.*
