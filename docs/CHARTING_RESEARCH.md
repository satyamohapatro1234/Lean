# Charting Library Research — Complete Findings

## TradingView Products: Full Breakdown

### 1. TradingView Widgets (Free, no application needed)
- Copy-paste embeds
- No custom data feed possible
- No drawing tools
- Good only for simple price display
- NOT usable for our platform

### 2. TradingView Lightweight Charts (Apache 2.0, fully open source)
- GitHub: https://github.com/tradingview/lightweight-charts
- 45KB, very fast
- Limited drawing tools (none built-in)
- NO built-in indicators
- Good for simple price line charts only
- Would need heavy custom work for drawing tools

### 3. TradingView Advanced Charts (FREE for public web projects)
- Must apply: https://www.tradingview.com/advanced-charts/
- 100+ built-in indicators
- 80+ drawing tools (Fibonacci, Gann, channels, rays, etc.)
- Requires: TradingView branding/attribution
- License restriction: NOT for private/personal/internal use
- Our project IS a public web project — we can apply
- Risk: approval not guaranteed, can be revoked
- Enterprise/commercial: separate paid license

### 4. TradingView Trading Platform (Commercial license)
- Includes order ticket, DOM trading
- For actual broker integrations
- Paid only

## Decision: KLineChart Pro as Primary

### Why KLineChart Pro Wins
- Apache 2.0 license — zero restrictions
- https://github.com/klinecharts/KLineChart (3,591 stars)
- https://github.com/klinecharts/pro (Apache 2.0)
- Built-in indicators: MA, EMA, BOLL, MACD, RSI, KDJ, OBV, SAR, and more
- Full drawing tools: all standard trading drawing tools
- Zero dependencies
- TypeScript support
- Mobile-compatible
- Datafeed API structure matches TradingView (easy future migration if TV license approved)
- Actively maintained

### KLineChart Built-in Indicators
Overlap studies: MA, EMA, SMA, BOLL, SAR, BIAS
Momentum: MACD, RSI, KDJ, CCI, DMI, ROC, MTM, VR, OBV
Drawing: trend lines, rays, price notes, channels, Fibonacci retracements,
         Fibonacci fans, Fibonacci circles, Fibonacci spirals,
         Fibonacci time zones, Gann fans, Gann squares, parallel channels

### Custom Indicator Integration
TA-Lib computes indicator in Python → sends via WebSocket → KLineChart renders:
```javascript
// Register custom indicator in KLineChart
chart.registerIndicator({
  name: 'SPIDER_WAVE',
  calc: (dataList) => dataList.map(d => ({ value: d.close })),
  draw: ({ ctx, visibleRange, indicator, xAxis, yAxis }) => {
    // Custom drawing from WebSocket data
  }
})
```

## Technical Indicators Stack

### Python Backend: TA-Lib
- License: BSD (free for open-source and commercial)
- 150+ indicators, 60+ candlestick patterns
- C implementation: 2-4x faster than pandas-ta
- Now has binary wheels: `pip install ta-lib` (no C compile needed)
- Use: strategy development, backtesting, research

### Frontend: KLineChart built-in
- No additional library needed
- Push custom indicator data via WebSocket

### Research/Notebooks: pandas-ta-classic
- 150 indicators + 62 candlestick patterns
- Community maintained fork of pandas-ta
- Good for Jupyter research environment

## What Zerodha/Dhan/Angel Use
From AlgoLoop analysis + industry knowledge:
- Most Indian brokers use TradingView Advanced Charts (with paid or approved free license)
- They have formal agreements with TradingView
- We cannot replicate their exact TradingView integration without similar agreement
- Our KLineChart Pro approach gives same visual quality and features freely

