# ETN 5m Gann HiLo branch-local simulated admission

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session: 2026-05-24

Use this when a same-root simulated-feedback replay finally materializes an
actionable execution candidate and mature structural validation, but still has
not completed practical extension.

## Exact branch

`TrendExpansion -> ElectricalEquipmentGannHiloActivator -> gann_hilo_activator -> ibkr_etn_electrical_equipment_gann_hilo_activator_5m_quality_exact_v1`

Provider, symbol, sector, and timeframe are labels only:

- provider: `IBKR`
- market/product: `US_EQ` / `single_stock/electrical_equipment`
- symbol: `ETN`
- exact timeframe: `5m`

## Evidence packets

Source Gate 1 root:

`/private/tmp/ict-engine-ibkr-etn-electrical-equipment-gann-hilo-activator-1m-mtf-gate1-20260524T022336+0800`

Exact downstream fail-closed root:

`/private/tmp/ict-engine-ibkr-etn-electrical-equipment-gann-hilo-activator-1m-mtf-gate1-20260524T022336+0800/downstream-exact-etn5m-gann-hilo-quality-20260524T030754+0800`

Simulated-admission root:

`/private/tmp/ict-engine-ibkr-etn-electrical-equipment-gann-hilo-activator-1m-mtf-gate1-20260524T022336+0800/simulated-trade-admission-etn5m-gann-hilo-quality-20260524T044236+0800`

Full-MTF context replay root:

`/private/tmp/ict-engine-ibkr-etn-electrical-equipment-gann-hilo-activator-1m-mtf-gate1-20260524T022336+0800/full-mtf-context-replay-etn5m-gann-hilo-quality-20260524T061621+0800`

Primary metrics:

- `checks/simulated_trade_admission_metrics.json`
- `summaries/terminal_decision_summary.md`
- `checks/prompt_to_artifact_checklist.csv`
- Fresh official readbacks:
  `policy-training-status --output-format json`, `workflow-status --refresh`,
  and `execution_tree_trace.json`

## Gate 1 survivor

Selected exact row:

- `ETN/5m/quality`
- package: `ibkr-etn-electrical-equipment-gann-hilo-activator-5m-quality-v1`
- trades: `123`
- density: `1.921875/day`
- raw: `+18.65%`
- `2bps/side`: `+13.73%`
- `5bps/side`: `+6.35%`

The `1m` origin did not pass hard `5bps/side`; this exact `5m` branch is a
separate higher-timeframe lane, not a rescue of the failed `1m` origin.

## Simulated feedback result

Same-Auto-Quant-workspace simulated trades:

- rows: `123`
- wins/losses/breakevens: `53/70/0`
- all `19/19` downstream commands exited `0`
- no command timed out
- exact branch survived: `true`
- ranker validation ready: `true`
- execution candidate actionable: `true`
- execution candidate status: `execution_ready`
- closed-loop branch admission status: `admitted`
- closed-loop branch admission reason:
  `exact_structural_branch_ready_and_actionable`
- execution tree gate status: `ready`
- execution tree branch: `fill_viable`
- execution readiness: `0.67`
- transition hazard: `0.3692625258022143`
- PDA hybrid alignment: `true`
- path-ranker score visible to execution tree: `true`
- path-ranker score used by execution tree: `true`

Structural validation matured on the official policy readback:

- `mature_rows=4`
- `history_mature_rows=127`
- `raw_scored_mature=127/30`
- `production_validation=127/30`
- `observation_validation=123/30`
- `ranker_runtime_status=enabled_candidate_set_ready`
- `trainer_status=runtime_eligible`
- `runtime_matches=3`

Remaining blockers:

- entry-model feedback training matched `0` rows and reported
  `auto_quant_real_trade_feedback_rows_missing`
- consumed-history validation stayed insufficient
- `extension_complete=false`

## Full-MTF context replay

The follow-up local-only replay copied the admitted state and ran `analyze
--data-root` over canonical retained ETN siblings for the full available ladder:

- `1m=11700`
- `5m=4992`
- `15m=1664`
- `30m=832`
- `1h=448`
- `4h=585`
- `1d=501`

Commands all exited `0` with no timeout:

- `analyze --data-root`
- `workflow-status --refresh`
- `pre-bayes-status --refresh`
- `policy-training-status`

Official readbacks preserved branch-local admission:

- `closed_loop_branch_admission.status=admitted`
- `candidate_status=execution_ready`
- `execution_candidate_actionable=true`
- `execution_readiness=0.67`
- `transition_hazard=0.36039984621299503`
- `pda_hybrid_alignment=true`
- `ranker_validation_ready=true`
- `path_ranker_score_visible_to_execution_tree=true`
- `path_ranker_score_used_by_execution_tree=true`
- `raw_scored_mature=127/30`
- `production_validation=127/30`
- `observation_validation=123/30`

Full-MTF decision:

- `etn5m_gann_hilo_full_mtf_context_replay_preserved_branch_local_admission_extension_progress`
- `branch_local_admitted=true`
- `promotion_allowed=branch_local_only`
- `trade_usable=false`
- `extension_complete=false`

Decision:

- `etn5m_gann_hilo_branch_local_simulated_admission_extension_candidate`
- `branch_local_admitted=true`
- `promotion_allowed=branch_local_only`
- `trade_usable=false`
- `update_goal=false`

## Operating rule

This is the positive counterpart to earlier SI/M2K simulated-feedback failures:
same-root simulated feedback can repair actionability, readiness, PDA alignment,
ranker validation, and execution-tree score use. It can even mature structural
ranker validation. That still is not enough for practical/live status when
consumed validation, entry-model feedback, full-MTF context, sibling/provider
breadth, and extension completion are not proven.

Classify this pattern as `branch_local_admitted_extension_candidate`. The
full-context replay step is now complete for the retained ETN ladder, but it is
only one extension step. The next useful work is sibling-symbol, product-class,
provider-parity, consumed-validation, and entry-model breadth. Do not call the
branch live-ready, rescue the failed lower-timeframe origin, rerun duplicate
simulated feedback, or lower extension gates.
