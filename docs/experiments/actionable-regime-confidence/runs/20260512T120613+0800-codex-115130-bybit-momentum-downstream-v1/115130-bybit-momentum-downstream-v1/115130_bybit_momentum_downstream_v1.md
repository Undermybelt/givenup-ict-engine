# 115130 Bybit Momentum Downstream v1

Run id: `20260512T120613+0800-codex-115130-bybit-momentum-downstream-v1`
Source six-provider AQ root: `20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1`
Symbol: `B2R_115130_BYBIT_BTC_MOMENTUM`
Branch: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`

## Source Slice
- Chosen source branch: `bybit_public` / `ProviderCryptoMomentumStateV1`.
- AQ metrics: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
- Normalized real-trade rows: `34` (`wins=14`, `losses=20`).
- Provider data rows: 1h `985`, 4h `247`, 1d `42`.

## Chain Results
- All command exits zero: `False`.
- Ingest status: `applied`, trades_applied `34`, feedback_records_inserted `34`.
- Pre-Bayes gate: `pass_neutralized`, policy_present `True`, soft_evidence `True`.
- Structural target rows: latest `4`, history `37`, CatBoost scores `0`.
- Execution status: `execution_blocked`, ready `False`, actionable `False`, review `None`.

## Decision
- Gate result: `downstream_chain_incomplete_fail_closed`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
- This downstream slice is real evidence for the ordered chain, but it is not strict Board A completion because it uses one selected 115130 branch, lacks explicit selected-history/source-control approval, and still must satisfy full per-regime cross-market/timeframe/period validation.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T120613+0800-codex-115130-bybit-momentum-downstream-v1/115130-bybit-momentum-downstream-v1/115130_bybit_momentum_downstream_v1.json`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T120613+0800-codex-115130-bybit-momentum-downstream-v1/115130-bybit-momentum-downstream-v1/115130_bybit_momentum_strategy_library_v1.json`
- Normalized trades: `docs/experiments/actionable-regime-confidence/runs/20260512T120613+0800-codex-115130-bybit-momentum-downstream-v1/115130-bybit-momentum-downstream-v1/115130_bybit_momentum_real_trades_v1.jsonl`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T120613+0800-codex-115130-bybit-momentum-downstream-v1/command-output`
- Exit markers: `docs/experiments/actionable-regime-confidence/runs/20260512T120613+0800-codex-115130-bybit-momentum-downstream-v1/checks`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T120613+0800-codex-115130-bybit-momentum-downstream-v1/state_115130_bybit_momentum_downstream_v1`
- CatBoost scores: `docs/experiments/actionable-regime-confidence/runs/20260512T120613+0800-codex-115130-bybit-momentum-downstream-v1/catboost/history_scores.csv`
