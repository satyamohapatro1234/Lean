# AI Agents — LangGraph + Claude API

**Status: Phase 3–5**

9 AI agents built with LangGraph, using Claude API online and Qwen via Ollama for offline operation.

## Agent Inventory

| Agent | Phase | Purpose |
|-------|-------|---------|
| BacktestOrchestrator | 3 | Natural language → structured backtest → formatted report |
| RiskMonitor | 3 | Background task: live drawdown watch + auto-liquidate at 5% |
| OptimizerAgent | 3 | Parameter optimization with LEAN + Monte Carlo validation |
| WaveSignal | 4 | Spider MTF hierarchy → options structure recommendation |
| StrategyAdvisor | 4 | Market view → specific strike selection + payoff analysis |
| NewsAnalyst | 5 | NSE announcements → portfolio impact summary |
| OrderAssist | 5 | Natural language → verified order parameters → execute |
| MarketScan | 5 | F&O universe scan for unusual OI/IV/volume patterns |
| PortfolioCoach | 5 | Portfolio health: correlation, concentration, expiry risk |

## Architecture

All agents share a common state schema via LangGraph. Human-in-the-loop approval is required before any live order is placed — the agent proposes, the trader confirms.

**AI model routing:**
- Online (internet available): Claude API (claude-sonnet-4-6)
- Offline (local): Qwen 2.5 Coder 32B via Ollama (RTX 3060, 12GB VRAM)

## MCP Server

The BacktestOrchestrator, RiskMonitor, and OptimizerAgent are exposed as Claude Desktop tools via a FastMCP server.

```bash
# Run MCP server
python agents/mcp_server.py

# Test from Claude Desktop
"Run Spider Wave backtest on NIFTY for the last 3 years with Euler optimization"
```
