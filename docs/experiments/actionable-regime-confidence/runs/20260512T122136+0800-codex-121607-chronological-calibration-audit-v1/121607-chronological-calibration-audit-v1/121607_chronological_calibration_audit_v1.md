# 121607 Chronological Calibration Audit v1

Run id: `20260512T122136+0800-codex-121607-chronological-calibration-audit-v1`
Source feedback packet: `20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1`
Source post-chain rows: `20260512T121542+0800-codex-120630-115700-layered-postchain-validator-v1`

## Result
- Rows audited: `237`.
- Providers: `6`; branches: `2`; chronological periods: `3`.
- Symbols: `['B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700']`.
- Active structural regime/confidence: `range` / `0.5250864595751618`.
- Max market-regime probability: `0.7476877176681956`.
- CPD loss-probability delta candidate: `0.362116`.
- Execution ready/actionable/review: `False` / `False` / `observe`.

## Gate
- Cross-provider ready: `True`.
- Cross-period ready: `True`.
- Cross-instrument ready: `False`.
- Board regime >=95 ready: `False`.
- Production mutation allowed: `false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Decision
- The `121607` feedback packet is chronologically and cross-provider auditable, but it is still single-instrument BTC evidence and the active regime confidence remains far below the Board A 95% threshold.
- Treat the empirical loss shift as candidate likelihood evidence for smoothing/backtest queues only; do not overwrite production BBN CPDs or execution weights from this packet alone.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T122136+0800-codex-121607-chronological-calibration-audit-v1/121607-chronological-calibration-audit-v1/121607_chronological_calibration_audit_v1.json`
- Period summary: `docs/experiments/actionable-regime-confidence/runs/20260512T122136+0800-codex-121607-chronological-calibration-audit-v1/derived/chronological_period_summary.csv`
- Provider summary: `docs/experiments/actionable-regime-confidence/runs/20260512T122136+0800-codex-121607-chronological-calibration-audit-v1/derived/provider_summary.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260512T122136+0800-codex-121607-chronological-calibration-audit-v1/derived/branch_summary.csv`
- Provider-period summary: `docs/experiments/actionable-regime-confidence/runs/20260512T122136+0800-codex-121607-chronological-calibration-audit-v1/derived/provider_period_summary.csv`
- Branch-period summary: `docs/experiments/actionable-regime-confidence/runs/20260512T122136+0800-codex-121607-chronological-calibration-audit-v1/derived/branch_period_summary.csv`
