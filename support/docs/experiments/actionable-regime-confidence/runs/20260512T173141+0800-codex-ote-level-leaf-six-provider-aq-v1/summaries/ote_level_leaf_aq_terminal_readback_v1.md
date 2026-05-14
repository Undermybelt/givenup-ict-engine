# 173141 OTE Level-Leaf AQ Terminal Readback v1

Generated: 2026-05-12 17:44:40 +0800

Source claim: `173141_ote_level_leaf_six_provider_aq_packet_v1`

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T173141+0800-codex-ote-level-leaf-six-provider-aq-v1/`

State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T173141+0800-codex-ote-level-leaf-six-provider-aq-v1/state`

## Preflight

- Provider/material rows: `6/6`
- Provider set: `yfinance/YF`, `Binance`, `Bybit`, `Kraken`, `IBKR`, `TradingViewRemix/TVR local-stdio`
- Agent material count: `6`
- OTE branch leaves preserved: `4/4`
- Material timerange: `20250101-20260512`

## AQ Commands

- `07_auto_quant_agent_material_batch.exit`: `0`
- `08_auto_quant_agent_material_dispatch.exit`: `0`
- `09_auto_quant_agent_material_rank.exit`: `0`

Artifacts:

- Batch: `auto-quant-agent-material-batch:PROVIDER_OTE_173141:20260512T094245.022Z`
- Dispatch: `auto-quant-agent-material-dispatch:PROVIDER_OTE_173141:20260512T094311.198Z`
- Rank: `auto-quant-agent-material-rank:PROVIDER_OTE_173141:20260512T094313.799Z`

## Rank Readback

| Provider unit | Status | Trades | Win rate | Sharpe | Total profit |
|---|---:|---:|---:|---:|---:|
| IBKR SPY 1h | completed | 6 | 33.3333% | 0.1297 | 0.54% |
| Binance BTCUSDT 1h | completed | 0 | 0.0% | 0.0 | 0.0% |
| Bybit BTCUSDT 1h | completed | 0 | 0.0% | 0.0 | 0.0% |
| Kraken XBTUSD 1h | completed | 0 | 0.0% | 0.0 | 0.0% |
| TVR BTC-USD 1h | completed | 0 | 0.0% | 0.0 | 0.0% |
| yfinance/YF SPY 1h | completed | 3 | 0.0% | -0.2454 | -2.4% |

## Decision

Fail closed. AQ consumed the same-root OTE provider material, but the result is not branch-keyed portable profitability evidence: one thin mildly positive IBKR unit, one thin negative YF unit, and four zero-trade provider units. No Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree continuation should run from this packet.
