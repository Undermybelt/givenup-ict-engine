# Tomac NQ Nonzero Downstream Schema Fix v2

Run id: `20260512T002251+0800-codex-board-b-local-nq-nonzero-candidate-probe-v1`

## Decision

This is supplemental Board B evidence only. It fixes the local wire schema and proves the 9-trade NQ candidate can be ingested, but it does not promote the candidate.

- Packet decision: `fail:measured_nonzero_but_branch_rc_spa_rejected`
- Stable profit score: `17.1500`
- Auto-Quant candidate: `TomacNQ_KillzoneBreakout`
- Trade rows: `9`
- Root counts: `Bull=0`, `Bear=6`, `Sideways=3`, `Crisis=0`

## Root Cause

The generated JSONL used invalid factor-direction tokens inside `factors_used`.

- Before fix: `trades_applied=0`, `trades_invalid=9`
- Invalid tokens: `long` for the strategy factor, and `Sideways` for root-context factor rows
- Wire contract: `factors_used[*].direction` must be `Bull`, `Bear`, or `Neutral`

## Fix

Patched only the run-local packet builder:

`docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/scripts/build_tomac_nq_nonzero_packet_v1.py`

Normalization:

- root `Bull/Bear` remains directional
- root `Sideways/Crisis/Unlabeled` maps to `Neutral`
- PnL-positive factor rows map to `Bull`
- PnL-negative factor rows map to `Bear`
- zero-PnL factor rows map to `Neutral`

## Verification

- Dry-run after fix: `trades_applied=9`, `trades_invalid=0`
- Fresh copied state: `state_tomac_nq_nonzero_v2`
- Actual ingest after fix: `ledger_status=applied`, `feedback_records_inserted=9`, `trades_applied=9`, `trades_invalid=0`
- Pre-Bayes: `pass_neutralized`
- CatBoost/path-ranker: runtime ready, `enabled_candidate_set_ready`, `runtime_matches=1`
- Structural bundle: still selected prior `220646` Crisis branch, not this Tomac NQ branch
- Execution candidate: `candidate_status=ready`, `review_status=observe`, not promotion
- Workflow full status: `blocking_status=blocked`, `blocking_reason=user_selected_historical_data_missing`
- Provider status: yfinance and Kraken CLI ready; IBKR gateway/deps and TradingViewRemix remain unhealthy

## Artifacts

- Fixed wire: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/ict-engine-downstream/tomac_nq_nonzero_candidate_real_trades_v1.jsonl`
- Before-fix repro: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/ict-engine-downstream/ingest_schema_repro_before_fix_v1.out`
- After-fix dry-run: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/ict-engine-downstream/ingest_schema_repro_after_fix_v1.out`
- After-fix apply: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/ict-engine-downstream/ingest_apply_after_schema_fix_v2.out`
- Pre-Bayes: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/ict-engine-downstream/pre_bayes_status_after_schema_fix_v2.out`
- Policy/path-ranker: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/ict-engine-downstream/policy_training_status_after_schema_fix_v2.out`
- Workflow full: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/ict-engine-downstream/workflow_status_after_schema_fix_v2.out`

## Next

Keep this as fail-closed schema/measurement evidence. It resolves the `0/9 invalid` ingest bug for this run, but promotion remains blocked by weak RC-SPA support, no Bull/Crisis coverage, observe-only execution-candidate status, and `user_selected_historical_data_missing`.
