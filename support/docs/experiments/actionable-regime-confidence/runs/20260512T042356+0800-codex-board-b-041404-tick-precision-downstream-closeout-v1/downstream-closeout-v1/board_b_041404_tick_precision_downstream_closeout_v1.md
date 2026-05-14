# Board B 041404 Tick Precision Downstream Closeout v1

Run id: `20260512T042356+0800-codex-board-b-041404-tick-precision-downstream-closeout-v1`

This is an append-only readback of the completed copied-state downstream probe
for the `041404` tick-precision LTF diagnostic. It does not edit the Current
Cursor, does not select historical data, does not promote the sidecar, and does
not call `update_goal`.

## Scope

The completed probe copied the `032157/downstream-combined-v1` state into
`041404/state_tick_precision_v1`, materialized the tick-precision diagnostic
packet, and ran ict-engine downstream commands against that copied state.

## Evidence

- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/06_auto_quant_results_import.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/07_auto_quant_prior_init.err`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/08_auto_quant_ingest_real_trades.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/09_pre_bayes_status.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/10_policy_training_status.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/11_export_structural_path_ranking_target.out`

## Readback

- `06_auto_quant_results_import.exit=0`; strategy library import accepted `2/2`
  strategies with `n_error=0`.
- `07_auto_quant_prior_init.exit=1`; prior-init refused to stack on an existing
  copied-state BBN prior from library
  `auto_quant_strategy_library_B2R_NQ_COST_CRISIS_REPAIR_032157_20260511T194002.337410000Z`.
- `08_auto_quant_ingest_real_trades.exit=0`; real-trade ingest applied `4/15`
  tick-precision rows, rejected `11` invalid rows, and inserted `4` feedback
  records.
- `09_pre_bayes_status.exit=0`; Pre-Bayes remained a readback surface, not a
  promotion decision.
- `10_policy_training_status.exit=0`; path-ranker remained uncalibrated with
  `raw_scored_mature=0/30`, `production_validation=0/30`, and
  `observation_validation=0/30`.
- `11_export_structural_path_ranking_target.exit=0`; export emitted `5`
  candidate rows and `10` history rows, but `mature_rows=0` and all candidate
  reward states stayed `unobserved`.

## Gate

- `diagnostic_only:agent_selected_ltf_tick_precision_downstream_probe`
- `fail_closed:prior_init_refused_existing_bbn_prior`
- `fail_closed:real_trade_ingest_partial_4_of_15_invalid_11`
- `fail_closed:path_ranker_validation_0_of_30`
- `blocked:user_selected_historical_data_missing`

## Next

Do not promote from this copied-state LTF sidecar. If this precision shape is
used after explicit user selection, start from a clean selected-data state or
intentionally roll back the copied BBN prior before prior-init; then advance
only if the selected run produces nonzero mature rooted branch observations for
Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
