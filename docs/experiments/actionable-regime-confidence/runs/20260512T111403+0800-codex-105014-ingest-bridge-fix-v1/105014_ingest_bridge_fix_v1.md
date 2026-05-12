# 105014 Ingest Bridge Fix v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T111403+0800-codex-105014-ingest-bridge-fix-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T105014+0800-codex-104610-btc-pullback-downstream-readback-v1`

Symbol: `B2R_YAHOO_CRYPTO_BTC_PULLBACK_104610`

## Result

Gate: `105014_ingest_bridge_fix_v1=real_trades_ingested_observation_floor_met_but_pre_bayes_empty_target_rows_unscored_execution_fail_closed_no_promotion`

This run repaired the real-trade ingest bridge for the 104610/105014 BTC pullback branch, but it is not promotion evidence.

## Evidence

- `01_ingest_real_trades_dry_run.exit=0`
- `02_ingest_real_trades_force.exit=0`
- `03_pre_bayes_status.exit=0`
- `04_policy_training_status.exit=0`
- `05_export_structural_path_ranking_target.exit=0`
- `06_workflow_structural_bundle.exit=0`
- `07_workflow_execution_candidate.exit=0`
- `08_workflow_full.exit=0`
- `09_policy_training_status_after_export.exit=0`

## Readback

- Dry run previewed `146/146` rows with `0` invalid rows.
- Forced ingest applied `146/146` rows, inserted `146` feedback records, and wrote BBN state under `state_ingest_bridge_fix_v1/B2R_YAHOO_CRYPTO_BTC_PULLBACK_104610/bbn_network.json`.
- Pre-Bayes remained empty: no bridge, policy, soft evidence, filtered assignments, gate status, posterior probabilities, or canonical structural regime were present.
- Structural target export produced `2` rows, `2` history rows, `1` mature row, and `1` history mature row.
- Feedback observation validation passed with `146/30` mature observations and outcome distribution `loss=80`, `win=66`.
- CatBoost/path-ranking stayed non-promotable: `raw_scored_mature=0/30`, `production_validation=0/30`, calibration `not_fitted`, trainer artifact `missing`, runtime selection `disabled`.
- Execution stayed fail-closed: selected path `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1`, posterior `0.4520547945205479`, selected path probability `0.7508532423208192`, ready `false`, actionable `false`, review status `observe`, and closed-loop branch admission `fail_closed`.

## Decision

Accepted rows added `0`. Mature rooted branch observations promoted `0`. Source/control evidence acquired `false`. Explicit selected-history `false`. Canonical merge `false`. Selected-data AutoQuant promotion `false`. Downstream promotion `false`. Strict full objective `false`. Trade usable `false`. Promotion allowed `false`. `update_goal=false`.

## Next

Do not promote this branch from ingest alone. The next useful slice is a bridge/policy repair that turns the 146 feedback observations into scored mature target rows and a fitted path-ranker, then reruns Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree on the same rooted branch.
