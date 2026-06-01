# MYM 1m Qstick body momentum Gate 1 negative (2026-05-20)

## Context
- Branch path: `FUTURES -> equity_index -> MYM -> 1m -> CandleBodyMomentum -> QstickBodyMomentum -> ibkr_mym1m_qstick_body_momentum_7d_gate1_v1`
- Run root: `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260520T130812+0800-codex-ibkr-mym1m-qstick-body-momentum-7d-gate1-v1`
- Evidence file: `checks/terminal_metrics.json`
- Provider: retained real IBKR `MYM 202606` `1m` `7 D`, `9433` rows.

## Gate 1 result
All variants failed real-cost stress despite adequate raw activity:

| row | trades | raw | 1bps/side | 2bps/side | 5bps/side |
|---|---:|---:|---:|---:|---:|
| `MYM/qstick_reversal/1m` | 17 | +0.33% | -0.01% | -0.35% | -1.37% |
| `MYM/qstick_balanced/1m` | 58 | +0.15% | -1.01% | -2.17% | -5.65% |
| `MYM/qstick_dense/1m` | 71 | +0.32% | -1.10% | -2.52% | -6.78% |
| `MYM/qstick_quality/1m` | 36 | +0.04% | -0.68% | -1.40% | -3.56% |

## Decision
- `decision=drop_or_block_gate1_practical`
- `downstream_allowed=false`
- `pre_bayes_allowed=false`
- `bbn_allowed=false`
- `catboost_allowed=false`
- `execution_tree_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`

## Reusable lesson
Qstick/candle-body momentum can produce enough trades on MYM 1m, but the raw edge is too thin and collapses at `1bps/side`. Treat as a clean Gate 1 negative for the exact `MYM/1m/CandleBodyMomentum/QstickBodyMomentum` cell. Do not downstream or threshold-tune this cell unless a future hypothesis materially increases per-trade excursion before cost stress.
