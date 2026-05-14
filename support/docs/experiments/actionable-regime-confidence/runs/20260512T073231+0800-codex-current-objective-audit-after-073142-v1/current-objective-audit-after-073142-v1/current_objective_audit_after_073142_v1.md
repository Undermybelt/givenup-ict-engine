# Current Objective Audit After 073142 v1

Run id: `20260512T073231+0800-codex-current-objective-audit-after-073142-v1`

Gate result: `current_objective_audit_after_073142_v1=not_complete_source_control_and_downstream_gates_blocked`

Generated at: `2026-05-12T07:36:04+0800`

Current board hash observed while writing this packet: `9d557dbac98ec9959fe9e6092e06330c9e54d5a48c897c2ffe0c83dc5ef5277b`.

## Objective Restatement

Board A is not complete until every active `MainRegimeV2` root regime has its own 95%+ calibrated evidence packet, cross-instrument/cross-period/cross-market validation, and a real local chain readback through provider status, Auto-Quant, filter / Pre-Bayes / BBN, CatBoost or path-ranking, and workflow / execution-tree surfaces. Direct `Manipulation` remains a separate source/control gate and cannot be promoted from public metadata, OHLCV proxies, or same-exhibit controls without explicit approval.

This audit is read-only. It does not mutate R3/R5/R6 target roots, approve R6 RECAP/PACER provenance or `FLIP` controls, run direct verifier, run split calibration, canonical merge, selected-data AutoQuant promotion, make a trade claim, or call `update_goal`.

## Command Evidence

All captured command exits in this root are now `0`:

- `provider_status_agent`
- `auto_quant_status`
- `pre_bayes_status_nq`
- `workflow_status_nq_agent`
- `export_structural_path_ranking_target_nq`
- `policy_training_status_nq`
- `r6_approval_package_readback`
- `root_presence`
- `board_sha256`

Provider readback:

- Summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Ready: yfinance, `kraken_cli`, and built-in entry models.
- Not ready for the named provider requirement: IBKR bridge / IBKR market-data paths are dependency-unhealthy despite a reachable gateway; TradingView MCP is connectivity-unhealthy; public Kraken market-data path is dependency-unhealthy, while credentialed `kraken_cli` is ready.

Auto-Quant readback:

- Status: `dependency_ready_data_ready`.
- Managed workspace: `/tmp/ict-engine-board-a-064259-runtime-v1/auto-quant/.deps/auto-quant`.
- This proves runtime readiness only; it does not prove accepted regime confidence or source/control promotion.

Filter / Pre-Bayes / BBN readback:

- NQ Pre-Bayes exited `0`.
- Latest canonical structural active regime: `trend`.
- Latest canonical structural confidence: `0.9787037037037036`.
- Gate status: `pass_neutralized`.
- This is one NQ structural readback, not all root regimes and not cross-market/cross-period completion evidence.

CatBoost / policy-training / path-ranking readback:

- `policy-training-status` exited `0`.
- Entry-model training is not ready for either BBN or CatBoost: both entry models have `matched_rows=0`.
- Structural path-ranking runtime is disabled; calibration is `not_fitted`; trainer artifact is missing.
- Raw-scored mature rows: `0/30`; production validation rows: `0/30`; observation validation rows: `0/30`.
- `export-structural-path-ranking-target` exited `0`, but exported only `rows=1`, `mature_rows=0`, `rows_with_calibrated_path_prob=0`, and `rows_with_training_weight=0`.

Workflow / execution-tree readback:

- Workflow exited `0`, but `blocking_status=blocked` with `blocking_reason=user_selected_historical_data_missing`.
- Closed-loop branch admission is fail-closed: `actionable=false`, `execution_gate_status=execution_blocked`, `pre_bayes_gate_status=pass_neutralized`, and `review_status=observe`.

Source/control readback:

- `/tmp/ict-engine-board-a-r6-owner-export-v1`: absent.
- `/tmp/ict-engine-source-panel-recency-extension`: absent.
- `/tmp/ict-engine-native-subhour-source-label-intake`: exists, but prior settled board evidence keeps it TSIE-derived/quarantined and Crisis-absent.
- `/tmp/ict-engine-source-label-equivalence-intake`: exists, but non-target/non-promoting under prior board evidence.
- `/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid`: exists, but `approval_present=false`, `canonical_merge_allowed_now=false`, and `downstream_rerun_allowed_now=false`.
- R6 row materialization remains positive-candidate only: `positive_spoof_rows=5182`, `flip_rows=1553`, `matched_groups=1313`, isolated verifier status `schema_ready_unscored`; no explicit approval or source-owned normal controls are present.

## Decision

The strict objective is not achieved. Runtime surfaces can be called, but the evidence still fails the actual success criteria:

- Not every `MainRegimeV2` root has a 95%+ calibrated packet.
- Cross-market, cross-period, and cross-context validation is incomplete.
- R6 owner/export controls are absent and the approval package still has `approval_present=false`.
- R5 post-`2026-01-30` source-panel `MainRegimeV2` rows are absent.
- R3 verifier-native Crisis-capable native-subhour labels are absent.
- CatBoost / policy-training is not ready (`matched_rows=0`).
- Structural path-ranking has no mature/calibrated/training-weight rows.
- Workflow / execution tree remains blocked and observe-only.

Accepted rows added: `0`.
R6 owner/export unlock: `false`.
R5 recency unlock: `false`.
R3 native-subhour unlock: `false`.
Valid required-root unlock: `false`.
Source/control evidence acquired: `false`.
Direct verifier run: `false`.
Split calibration run: `false`.
Canonical merge: `false`.
Downstream promotion rerun: `false`.
Strict full objective: `false`.
Trade usable: `false`.
`update_goal=false`.

## Next

Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant promotion, filter / Pre-Bayes / BBN promotion, CatBoost/path-ranking promotion, or execution-tree promotion until one of these arrives: explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.
