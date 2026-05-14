# Board A AQ Feedback Bridge After 101221 v1

Run ID: `20260512T103013+0800-codex-board-a-aq-feedback-bridge-after-101221-v1`

## Source

- Source run: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2`
- Source metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/local-cache-seed-v2/auto_quant_metrics_summary.json`
- Source library: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/local-cache-seed-v2/strategy_library_local_cache_seed_v2.json`
- Board hash before run: `f61052b9562fcd2839a447a4b0a451711b604e8fa251583093433c7d100d602f`

## Result

- Auto-Quant threaded-DNS run exit: `0`.
- Backtests succeeded/failed: `8` / `0`.
- ict-engine import `n_ok`: `2`.
- BBN prior dry-run evidence gate: `True`; final probabilities `[0.6934000690615427, 4.901141743247006e-08, 0.3065998819270398]`.
- Discovery feedback is real but non-promoting: both strategies are tagged `unmapped_crypto_local_cache_seed_not_mainregimev2`, and no source/control unlock or selected-history approval exists.

## Gate

- Gate result: `board_a_aq_feedback_bridge_after_101221_v1=non_promoting_aq_feedback_imported_bbn_dryrun_root_unbound_no_unlock`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Source/control evidence acquired: `false`.
- Canonical merge: `false`.
- Downstream promotion: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

- Use this only as source-control search priority: BNB mean-reversion and SOL/BNB/AVAX crash-rebound windows are worth labeling with source-owned MainRegimeV2 roots and matched negatives. Do not rerun the same 101221 cached crypto AQ path for Board A acceptance.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T103013+0800-codex-board-a-aq-feedback-bridge-after-101221-v1/board-a-aq-feedback-bridge-after-101221-v1/board_a_aq_feedback_bridge_after_101221_v1.json`
- Decision gates: `docs/experiments/actionable-regime-confidence/runs/20260512T103013+0800-codex-board-a-aq-feedback-bridge-after-101221-v1/board-a-aq-feedback-bridge-after-101221-v1/bridge_decision_gates_v1.csv`
- Strategy metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T103013+0800-codex-board-a-aq-feedback-bridge-after-101221-v1/board-a-aq-feedback-bridge-after-101221-v1/strategy_timerange_metrics_v1.csv`
- Strategy metadata gates: `docs/experiments/actionable-regime-confidence/runs/20260512T103013+0800-codex-board-a-aq-feedback-bridge-after-101221-v1/board-a-aq-feedback-bridge-after-101221-v1/strategy_metadata_gate_v1.csv`
- Source-control priority feedback: `docs/experiments/actionable-regime-confidence/runs/20260512T103013+0800-codex-board-a-aq-feedback-bridge-after-101221-v1/board-a-aq-feedback-bridge-after-101221-v1/source_control_priority_feedback_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T103013+0800-codex-board-a-aq-feedback-bridge-after-101221-v1/checks/board_a_aq_feedback_bridge_after_101221_v1_assertions.out`
