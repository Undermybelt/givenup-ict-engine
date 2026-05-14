# 142321 NQ Sliced Downstream Readback v1

Root: `docs/experiments/actionable-regime-confidence/runs/20260512T142321+0800-codex-135318-nq-sliced-downstream-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T141000+0800-codex-135318-real-trades-downstream-v1`

## Command Evidence

- `01_slice_nq_json.exit=0`
- `02_slice_nq_mtf_json.exit=0`
- `03_slice_nq_htf_json.exit=0`
- `04_results_import.exit=0`
- `05_prior_init.exit=0`
- `06_ingest_real_trades.exit=0`
- `07_analyze_slice.exit=0`, `elapsed_seconds=29`, `exit_code=0`
- `08_pre_bayes_status.exit=0`
- `09_policy_training_status.exit=0`
- `10_export_structural_path_target.exit=0`
- `11_workflow_structural_bundle.exit=0`
- `12_workflow_execution_candidate.exit=0`
- `13_workflow_full.exit=0`

## Readback

- Data scope is a sliced local Tomac NQ replay: last `2000` 15m candles, last `1000` 1h candles, and last `500` 1d candles. This is not provider-owned acquisition and not a cross-market/provider validation packet.
- Pre-Bayes/BBN surfaced `latest_gate_status=pass_neutralized`, active structural regime `range`, structural confidence `0.5304098970495816`, and probabilities `range=0.7491786839446286`, `stress=0.17590344766090854`, `transition=0.07491786839446286`, `trend=0.0`.
- Bridge evidence stayed ambiguous: long/short signal probability gap was `0.0004815208994379816`, with selected entry quality `medium`.
- Structural path target export produced `rows=3`, `history_rows=3`, `mature_rows=1`, `rows_with_calibrated_path_prob=0`, and `rows_with_path_prob_lower_bound=0`.
- Policy training remained immature for BBN/CatBoost adoption: both `cisd_rb_long_v1` and `breaker_rb_long_v1` reported `matched_rows=0`, no win/loss label coverage, low bin diversity, and too little numeric feature variation.
- Structural path-ranking runtime remained disabled in `policy-training-status`: `runtime_selection=disabled`, `runtime_source=none`, `runtime_matches=0`.
- Execution candidate stayed blocked: `actionable=false`, `ready=false`, `candidate_status=execution_blocked`, `execution_gate_status=execution_blocked`, `review_status=observe`, `execution_readiness=0.3649376526590964`, `selected_path_probability=0.3622922020741514`, and no calibrated path probability or lower bound.
- `workflow-status --refresh` exposed promotion-supporting artifacts, but consumed validation was absent; this does not override execution blocking, ranker immaturity, or Board A acceptance gates.

## Decision

This root is valid support-only downstream plumbing evidence: the ordered Auto-Quant import/prior/trade-ingest -> analyze -> Pre-Bayes/BBN -> structural target export -> workflow/execution readback path completed on a bounded NQ slice.

It is not Board A acceptance evidence. It does not provide provider-owned acquisition, cross-instrument/provider validation, per-regime calibrated posterior/path lower bound `>=0.95`, CatBoost/path-ranker mature validation, or execution readiness/actionability.

Net Board A effect remains fail-closed: accepted `>=95%` contexts `0`; strict full objective false; trade usable false; promotion allowed false; and `update_goal=false`.
