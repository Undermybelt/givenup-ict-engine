# Board A Aggregated Rooted Feedback Ranker Packet - 2026-05-23

## Scope

- Board: A, rooted regime/subclass evidence only.
- Replay run: `support/docs/experiments/actionable-regime-confidence/runs/20260523T064708Z-codex-board-a-positive-negative-feedback-ingress-v1/`.
- Symbol bucket: `BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523`.
- Candidate set: `board-a-aggregated-rooted-positive-negative-feedback-v1`.
- Runner: `support/docs/experiments/actionable-regime-confidence/scripts/run_board_a_positive_negative_feedback_ingress_v1.py`.

This packet aggregates existing Board A Auto-Quant rank rows into one feedback
and structural path-ranker surface. It does not open a Board B profitability
lane. It does not register a root regime or make any trade-usable claim.

## Source Coverage

- Source rank artifacts: `14` existing `*board-a*` AQ rank JSON files.
- Source AQ rank rows: `47`.
- Positive Bayesian-evidence rows: `9`.
- Negative boundary rows: `38`.
- Unique structural path ids ingested: `47`.
- Branch families covered include `TrendExpansion` subclasses,
  `RangeConsolidation -> InsuranceDefensivePremiumCycle`, `BoardA ->
  CrossMarketRegime95`, and `BoardA -> IBKRIntradayOptions`.

## Executed Chain

- `emit-probe`: `47/47` feedback files emitted, all exits `0`.
- `ict-engine update --feedback-file`: `47/47` feedback rows ingested, all
  exits `0`.
- Initial readbacks exited `0`: `workflow-status`, `pre-bayes-status`,
  `policy-training-status`, and `export-structural-path-ranking-target`.
- External trainer ran on exported target CSV and trained CatBoost from `50`
  samples with label distribution `38` failure / `12` success.
- CatBoost scores were applied to `ict-engine` with
  `apply-structural-path-ranking-external-scores`, exit `0`.
- Trainer artifact was registered with
  `register-structural-path-ranking-trainer-artifact`, exit `0`.
- Runtime enable first failed on invalid `--reuse-mode prefer-history`, then was
  rerun with `--reuse-mode prefer_history`, exit `0`.
- Final readbacks exited `0`: `policy-training-status`, `workflow-status`, and
  `export-structural-path-ranking-target`.

## Final Ranker Readback

- `auto_quant_real_trade_entry_v1.ready=true`.
- `auto_quant_real_trade_entry_v1.matched_rows=47`.
- `structural_feedback_rows=47`.
- `outcomes=loss=38,win=9`.
- `structural_path_ranking_target rows=50`.
- `history_rows=188`.
- `mature_rows=50`.
- `history_mature_rows=185`.
- `raw_scored_mature=47/30`.
- `production_validation=120/30`.
- `observation_validation=47/30`.
- `calibration=evaluated`.
- `calibration_brier_score=0.0005668934240362831`.
- `calibration_expected_error=0.023809523809524835`.
- `trainer_artifact=ready`.
- `trainer_status=runtime_eligible`.
- `runtime_selection=enabled_candidate_set_ready`.
- `runtime_mode=prefer_history`.
- `runtime_source=candidate_set`.
- `score_model_family=catboost`.
- `score_source=external_model`.
- `runtime_matches=3`.

## Regime-Confidence Asset Inventory Bridge

After the aggregate feedback/ranker replay, the missing Board A regime-confidence
asset inventory was replayed into the same aggregate run root with:

- Command output:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T064708Z-codex-board-a-positive-negative-feedback-ingress-v1/command-output/50_regime_confidence_assets_inventory.out`.
- Follow-up readbacks:
  `command-output/51_workflow_status_after_assets.out`,
  `command-output/52_pre_bayes_status_after_assets.out`,
  `command-output/53_policy_training_status_after_assets.out`, and
  `command-output/54_export_after_assets.out`.
- Inventory artifact:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T064708Z-codex-board-a-positive-negative-feedback-ingress-v1/state/BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523/regime_confidence_asset_inventory.json`.

The inventory bridge exited `0` and repaired the prior missing-inventory surface:

- `regime_confidence_assets.inventory_status=ready`.
- `asset_count=18`.
- `board_a_regime_gate_count=11`.
- `direct_event_overlay_count=2`.
- `diagnostic_after_source_control_unlock_count=4`.
- `contrast_evidence_count=10`.
- `recovered_not_candidate_pack_count=9`.
- `promotion_allowed=false`.
- `runtime_selection_enabled=false`.

Representative recovered Board A gates are visible in the inventory:

- `bull_sourcebacked_drawdown_volatility_v1`: `Bull`, calibration Wilson 95 LCB
  `0.952516`, test Wilson 95 LCB `0.961931`, scope
  `index+single_stock;1d+1w`.
- `bear_sourcebacked_drawdown_return_ratio_v1`: `Bear`, calibration Wilson 95
  LCB `0.993968`, test Wilson 95 LCB `0.992722`, scope
  `crypto+equity_etf;1d+1w`.
- `sideways_sourcebacked_abs_return_range_v1`: `Sideways`, calibration Wilson
  95 LCB `0.988647`, test Wilson 95 LCB `0.995568`, scope-limited.
- `crisis_range_ratio_intraday_v1`: `Crisis`, calibration Wilson 95 LCB
  `0.996248`, test Wilson 95 LCB `0.995981`, scope-limited.
- `manipulation_telegram_direct_event_v1`: direct-event overlay, calibration
  Wilson 95 LCB `0.999735`, test Wilson 95 LCB `0.999701`, still not a
  full-coverage root promotion.

This repairs asset visibility only. It does not register a root class and does
not turn the aggregate bucket into a trade-usable or execution-promoted surface.

## State-Root Split Readback

The post-asset readbacks expose a split between the aggregate feedback/ranker
state and the recovered regime-confidence asset inventory:

- Feedback, learning state, BBN, and mature ranker evidence live under
  `state/ict-engine-feedback/BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523/`.
- Regime-confidence asset inventory and the post-asset workflow snapshot live
  under `state/BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523/`.
- A fresh export after the asset bridge exited `0` but read the top-level symbol
  root and returned only `rows=1`, `history_rows=1`, `mature_rows=0`, and
  `history_mature_rows=0`.
- The post-asset policy readback sees
  `regime_confidence_assets.inventory_status=ready` and `asset_count=18`, but
  it does not see the earlier mature structural path-ranking surface.
- The workflow readback sees a structural recommended path only as
  `candidate_status=execution_candidate_observed`, with
  `execution_readiness=null`, `path_ranker_raw_score=null`,
  `path_ranker_runtime_source=null`, `ready=false`, and `persisted=false`.

Root cause: the current CLI surfaces can make either the asset inventory or the
feedback/ranker maturity visible depending on which symbol root they read, but
this run has not unified both into one execution-tree-consumable surface.

Smallest next repair: make the aggregate Board A workflow read the recovered
asset inventory and the `ict-engine-feedback` ranker/training state through one
canonical symbol-root view, then rerun `workflow-status`, `pre-bayes-status`,
`policy-training-status`, `export-structural-path-ranking-target`, and execution
candidate/tree readbacks. Do not claim root `>=95%` bull/bear closure until that
combined surface also proves promotion/runtime gates.

## Policy/Export Root-Unification Repair

A minimal read-path repair now lets policy/export readbacks prefer the stronger
`state/ict-engine-feedback/<SYMBOL>/` structural ranker root when the top-level
`state/<SYMBOL>/` root only carries the recovered asset inventory or a weaker
ranker summary. This is intentionally read-only: it does not copy artifacts,
does not change feedback ingestion ownership, and does not promote any regime.

- Code path: `src/application/entry_models/training_export.rs`.
- Targeted regression:
  `cargo test -q application::entry_models::training_export::tests::policy_training_status_uses_mature_feedback_child_root_for_ranker_when_primary_root_only_has_assets`.
- Fresh policy readback:
  `command-output/55_policy_training_status_after_root_unification.out`, exit
  `0`.
- Fresh structural export:
  `command-output/56_export_after_root_unification.out`, exit `0`.
- Fresh workflow readback:
  `command-output/57_workflow_status_after_root_unification.out`, exit `0`.

The repaired top-level policy readback now shows both recovered Board A assets
and mature CatBoost/path-ranker evidence in one surface:

- `regime_confidence_assets.inventory_status=ready`.
- `regime_confidence_assets.asset_count=18`.
- `regime_confidence_assets.board_a_regime_gate_count=11`.
- `regime_confidence_assets.promotion_allowed=false`.
- `regime_confidence_assets.runtime_selection_enabled=false`.
- `structural_path_ranking_target.rows=50`.
- `history_rows=188`.
- `mature_rows=50`.
- `history_mature_rows=185`.
- `raw_scored_mature_rows=47`.
- `production_validation_rows=120`.
- `observation_validation_rows=47`.
- `calibration_ready=true`.
- `trainer_artifact_ready=true`.
- `runtime_selection_status=enabled_candidate_set_ready`.
- `runtime_source_kind=candidate_set`.
- `runtime_active_match_count=3`.
- `score_model_family=catboost`.
- `score_source_kind=external_model`.

The repaired export no longer falls back to the weak top-level `rows=1` state:

- `rows=50`.
- `history_rows=188`.
- `mature_rows=50`.
- `history_mature_rows=185`.
- `rows_with_raw_path_score=50`.
- `history_rows_with_raw_path_score=167`.
- `rows_with_calibrated_path_prob=3`.
- `history_rows_with_calibrated_path_prob=120`.
- `summary_path=.../state/ict-engine-feedback/BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523/policy_training/structural_path_ranking_target_summary.json`.

This closes the policy/export readback split only. Workflow/execution still
fails closed: the latest structural candidate remains
`candidate_status=execution_candidate_observed`, `ready=false`,
`execution_readiness=null`, `path_ranker_raw_score=null`,
`path_ranker_runtime_source=null`, and `closed_loop_branch_admission.status=fail_closed`.

## Remaining Blockers

Workflow is still fail-closed:

- `closed_loop_branch_admission.status=fail_closed`.
- `candidate_status=execution_blocked`.
- `execution_gate_status=execution_blocked`.
- `pre_bayes_gate_status=pass_neutralized`.
- `latest_execution_candidate=null`.
- `path_ranker_score_visible_to_execution_tree=null` at workflow/execution-tree
  level.
- `path_ranker_score_used_by_execution_tree=null` at workflow/execution-tree
  level.
- `regime_confidence_assets.inventory_status=ready` after the asset bridge.
- `regime_confidence_assets.promotion_allowed=false`.
- `regime_confidence_assets.runtime_selection_enabled=false`.
- Policy/export readbacks now unify the stronger `ict-engine-feedback` ranker
  root with top-level asset visibility, but workflow/execution candidate
  materialization still does not consume a path-ranker score.

## Decision

Keep as Board A aggregate feedback/ranker-maturity evidence. This is a real
upgrade over the earlier isolated feedback packets: observation, raw-scored,
production validation, calibration, trainer artifact, and runtime selection are
now all closed for the aggregate bucket.

It is still not Board A completion. It preserves positive/negative training
material, repairs aggregate CatBoost/path-ranker maturity in the
`ict-engine-feedback` root, repairs recovered regime-confidence asset visibility
in the top-level symbol root, and repairs the policy/export readback split
between those two surfaces. It does not yet prove a parent-root `>=95%`
bull/bear/regime confidence surface, does not produce an actionable execution
candidate, does not prove execution-tree consumption, does not register any root
regime, and is not trade-usable.

`update_goal=false`.
