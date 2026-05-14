# NQ Cost Crisis Repair V3 Cleanwire Apply Readback

Run id: `20260512T033508+0800-codex-board-b-nq-cost-crisis-repair-v3-cleanwire-apply-v2`

This is a compact assertion readback for the existing cleanwire apply state. It does not supersede the Board B cursor and it is not a promotion claim.

## Inputs

| Field | Value |
|---|---|
| Run root | `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3` |
| Fixed manifest | `downstream-v2/strategy_library_nq_cost_crisis_repair_v3_manifest_1_0.json` |
| Fixed real-trade wire | `downstream-v2/nq_cost_crisis_repair_real_trades_v3_wire_fixed.jsonl` |
| Clean apply state | `state_nq_cost_crisis_repair_v3_cleanwire_apply` |
| Upstream RC-SPA score | `90.0000` |
| Upstream hard gate | price roots `4/4` passed; `205047` Manipulation remains component-only |

## Readback

| Check | Evidence | Result |
|---|---|---|
| Command exits | `26-35` exit files all contain `0` | pass |
| Manifest import | fixed manifest imports with `manifest_version=1.0` | pass |
| Prior init | fixed manifest prior-init exits `0` | pass |
| Real-trade ingest | `trades_applied=15415`, `trades_total=15415`, `trades_invalid=0`, `content_hash=d2aec06adb0f4871` | pass |
| Pre-Bayes | `latest_gate_status=observe_only`, canonical structural regime `range`, confidence `0.3993185754313692` | fail-closed |
| Policy status before export | structural target export missing; runtime selection disabled | fail-closed |
| Structural target export | `rows=3`, `candidate_set_size=3`, `mature_rows=0`, calibrated rows `0`, training-weight rows `0` | fail-closed |
| Structural bundle | selected generic `range_mean_reversion` path, not the five exact aggregate-regime bundle paths | fail-closed |
| Execution candidate | `ready=false`, `actionable=false`, `candidate_status=execution_blocked`, `execution_readiness=0.3210541039505038` | fail-closed |
| Full workflow | `closed_loop_branch_admission.status=fail_closed`; blocking truth `user_selected_historical_data_missing` | fail-closed |

## Verdict

Cleanwire repair fixed the wire-level invalid row problem: all `15,415` rows applied with zero invalid trades. It did not produce a promotable downstream chain. The clean apply state collapsed back to a three-row generic structural target surface, Pre-Bayes remained `observe_only`, no mature/calibrated path-ranker rows existed, CatBoost was not trained for this clean state, and execution stayed blocked.

Promotion remains disallowed. The next non-duplicative closure run must combine:

- the wire-fixed all-valid trade JSONL,
- the exact aggregate-regime-bundle branch paths,
- CatBoost train/apply/register/runtime,
- explicit user-selected historical data,
- then Pre-Bayes/workflow/execution-tree admission.

