# Complete Book Reference — How Each Book Shaped the Plan

## Tier 1 — Must Read (Architecture Decisions)

### 1. Inside the Black Box (Narang, 3rd ed 2024)
- FREE summary: https://cdn.bookey.app/files/pdf/book/en/inside-the-black-box-by-rishi-k-narang.pdf
- Amazon: https://www.amazon.com/Inside-Black-Box/dp/1119931894
- **Impact on plan:** 4-component framework is the entire architecture spine
  - Without this: no risk model, no portfolio construction, just signals and execution
  - Key insight: "The portfolio construction model answers HOW MUCH, not WHAT"

### 2. Algorithmic Trading & DMA (Johnson, 2010)
- Internet Archive borrow: https://archive.org/details/algorithmictradi0000john
- Amazon: https://www.amazon.com/Algorithmic-Trading-DMA/dp/0956399207
- **Impact on plan:** Transaction cost model, VWAPExecution model choice
  - Without this: zero slippage assumption → live trading always loses

### 3. Building Winning Algo Trading Systems (Davey, 2014)
- Amazon: https://www.amazon.com/Building-Winning-Algorithmic-Trading-Systems/dp/1118778987
- GitHub (his Monte Carlo tool): look for companion website
- **Impact on plan:** Full 5-step validation sequence (IS→WFO→MC→OOS)
  - Without this: strategy passes IS backtest by luck, fails live

### 4. Machine Learning for Algorithmic Trading 2nd ed (Jansen, 2020)
- GitHub code: https://github.com/stefan-jansen/machine-learning-for-trading
- Amazon: https://www.amazon.com/Machine-Learning-Algorithmic-Trading/dp/1839217715
- **Impact on plan:** Data pipeline quality, corporate actions, FactorFiles
  - Without this: split-adjusted prices show false crashes → false signals

### 5. Advances in Financial Machine Learning (López de Prado, 2018)
- Amazon: https://www.amazon.com/Advances-Financial-Machine-Learning-Marcos/dp/1119482089
- **Impact on plan:** CPCV validation, HRP portfolio, why standard backtests lie
  - Key insight: standard WFO is insufficient for finance — CPCV handles non-IID data

## Tier 2 — Important (Design Decisions)

### 6. Systematic Trading (Carver, 2015)
- Amazon: https://www.amazon.com/Systematic-Trading/dp/0857194453
- **Impact on plan:** Forecast diversification, position sizing framework
  - Without this: correlated signals → over-concentrated positions

### 7. Advanced Futures Trading Strategies (Carver, 2023)
- Amazon: https://www.amazon.com/Advanced-Futures-Trading-Strategies/dp/0857199684
- **Impact on plan:** 30 tested strategies — our Phase 6 global strategy library
  - Key insight: most strategies fail when transaction costs are included

### 8. Machine Learning for Asset Managers (López de Prado, 2020)
- Amazon: https://www.amazon.com/Machine-Learning-Managers-Elements-Quantitative/dp/1108792898
- **Impact on plan:** HRP replaces Markowitz for portfolio construction
  - LEAN has RiskParityPortfolioConstructionModel built in — use it

### 9. Causal Factor Investing (López de Prado, 2023)
- Amazon: search Amazon
- **Impact on plan:** Find causes not correlations in alpha models
  - Relevant when extending Spider Wave with ML features in Phase 3+

## Tier 3 — Reference (Implementation Details)

### 10. Leveraged Trading (Carver, 2019)
- Amazon: https://www.amazon.com/Leveraged-Trading/dp/0857197215
- **Impact on plan:** Safe leverage calculation for Indian F&O
  - Key formula: target_leverage = target_risk / instrument_vol

### 11. Trading and Exchanges (Harris, 2002)
- Amazon (still relevant): https://www.amazon.com/Trading-Exchanges/dp/0195144708
- **Impact on plan:** Order type design, market microstructure for execution model

### 12. Professional Automated Trading (Durenard, 2013)
- Amazon: search Amazon
- **Impact on plan:** Full OMS architecture, event-driven design
  - How to structure the order lifecycle: create → submit → pending → fill/reject

## 2025 Research Papers (No purchase needed)

### Reinforcement Learning for Quantitative Trading (ACM 2023)
- URL: https://dl.acm.org/doi/pdf/10.1145/3582560
- **Finding:** PPO and SAC outperform rule-based strategies. RL agent integration is a valid Phase 3+ extension.

### From Deep Learning to LLMs in Finance (arXiv 2025)
- URL: https://arxiv.org/html/2503.21422v1
- **Finding:** LLM agents (QuantAgent, Alpha-GPT) are production-ready for strategy discovery. Validates our agent architecture.

