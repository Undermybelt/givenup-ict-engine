# 141000 1h/4h/1d Continuation Readback Fail-Closed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T141000+0800-codex-135318-real-trades-downstream-v1`

This is a late same-root continuation for checks `23-36`. It does not create a new evidence count for `141000`; it only records the bounded `1h/4h/1d` retry and downstream readbacks.

## Evidence

- NQ bounded analyze `23_nq_analyze_1h_4h_1d.exit=142`; stdout stayed empty.
- ES bounded analyze `30_es_analyze_1h_4h_1d.exit=142`; stdout stayed empty.
- NQ and ES Pre-Bayes readbacks exited `0`, but latest canonical structural regime, confidence, probabilities, filtered assignments, gate status, policy, and soft evidence were all absent.
- NQ policy training after the retry exited `0`, but `analyze_runs=0`, entry-model `matched_rows=0`, structural path-ranking runtime stayed disabled, raw-scored mature rows stayed `0/30`, production validation stayed `0/30`, trainer artifact was missing, and calibrated path probability/path lower bound were absent.
- ES policy training after the retry exited `0`, with the same fail-closed shape: `analyze_runs=0`, entry-model `matched_rows=0`, structural path-ranking runtime disabled, raw-scored mature rows `0/30`, production validation `0/30`, missing trainer artifact, and no calibrated path probability/path lower bound.
- NQ observation validation had `77/30` mature observations and ES had `115/30`, but those observation counts did not become calibrated production/path-ranker rows.
- NQ execution candidate stayed `ready=false`, `actionable=false`, `review_status=observe`, selected path probability `0.8290155440414507`, no calibrated path probability, and no path probability lower bound.
- ES execution candidate stayed `ready=false`, `actionable=false`, `review_status=observe`, selected path probability `0.7737704918032787`, no calibrated path probability, and no path probability lower bound.
- ES full workflow readback stayed fail-closed: `actionable_artifact_count=0`, `promotable_entries=0`, no consumed validation, no latest Pre-Bayes policy, and closed-loop branch admission `status=fail_closed`.

## Gate

- `support_same_root:141000_1h4h1d_continuation_readback_fail_closed_v1`.
- `same_root_detail_for:141000_real_trades_downstream_readback_v1`.
- `fail_closed:nq_analyze_1h4h1d_exit142`.
- `fail_closed:es_analyze_1h4h1d_exit142`.
- `fail_closed:pre_bayes_canonical_regime_absent`.
- `fail_closed:policy_training_analyze_runs_0`.
- `fail_closed:entry_models_matched_rows_0`.
- `fail_closed:path_ranker_runtime_disabled`.
- `fail_closed:raw_scored_mature_0_of_30`.
- `fail_closed:production_validation_0_of_30`.
- `fail_closed:calibrated_path_prob_absent`.
- `fail_closed:path_prob_lower_bound_absent`.
- `fail_closed:execution_ready_false`.
- `fail_closed:actionable_false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Decision

The bounded `1h/4h/1d` continuation confirms that the same `141000` full-root packet remains support-only and fail-closed. It does not satisfy per-regime `>=95%` calibrated confidence/lower-bound, cross-market/timeframe/provider validation, CatBoost/path-ranker calibration, or execution-tree admission. Count `141000` exactly once under the existing duplicate guard.
