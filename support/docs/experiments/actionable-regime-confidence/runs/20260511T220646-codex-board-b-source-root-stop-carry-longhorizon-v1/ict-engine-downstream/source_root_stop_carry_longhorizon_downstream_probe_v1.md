# Source Root Stop Carry Long-Horizon Downstream Probe v1

- Probe id: `20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-downstream-v1`.
- RC-SPA gate: `pass`; stable score `85.74074074074075`; price roots passed `4/4`; Manipulation component pass `True`.
- Real-trade wire: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/ict-engine-downstream/source_root_stop_carry_longhorizon_real_trades_wire_v1.jsonl` with `12329` records and branch paths preserved `True`.
- Real-trade ingest: `ingest_ok=True`, `trades_invalid=0`, `trades_total=12329`, `trades_applied=12329`.
- BBN state exists: `True`; learning state exists: `True`.
- Pre-Bayes: gate `None`, policy `None`.
- CatBoost/path-ranker policy readiness: `False`; summary `entry-model training modules mixed: ready=[] pending=[cisd_rb_long_v1,breaker_rb_long_v1] | structural path ranking target export missing runtime_selection=disabled runtime_source=none runtime_matches=0`.
- Workflow/execution-tree ready: `False`; workflow snapshot exists `True`.
- Structural path-ranking export exit: `0`.
- Downstream consumption: `consumed_through_bbn_feedback_readback;pre_bayes_policy_workflow_export_checked`.
- Promotion status: `not_promoted:execution_tree_or_policy_not_calibrated`.

Artifacts:
- `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/ict-engine-downstream/source_root_stop_carry_longhorizon_downstream_probe_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/ict-engine-downstream/source_root_stop_carry_longhorizon_downstream_probe_v1_assertions.out`
- logs under `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/ict-engine-downstream/logs`

Next:
- Do not call production promotion complete until execution-tree admissibility and calibrated path-ranker readiness are proven for the same branch paths.
