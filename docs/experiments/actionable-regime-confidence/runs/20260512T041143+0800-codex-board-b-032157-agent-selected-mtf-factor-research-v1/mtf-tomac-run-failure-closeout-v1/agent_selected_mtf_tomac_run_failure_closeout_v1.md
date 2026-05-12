# Agent-Selected MTF Tomac Run Failure Closeout v1

Scope: append-only readback for the completed `041143` MTF Auto-Quant follow-up.

This artifact does not edit the Board B cursor, does not satisfy `user_selected_historical_data`, and does not promote any candidate. It only records the completed direct external prepare plus the subsequent Tomac run failure.

## Evidence

- `command-output/03_prepare_external_direct.exit`
- `command-output/03_prepare_external_direct.out`
- `command-output/04_auto_quant_status_after_direct_prepare.exit`
- `command-output/04_auto_quant_status_after_direct_prepare.json`
- `command-output/05_auto_quant_run_tomac_mtf.exit`
- `command-output/05_auto_quant_run_tomac_mtf.out`
- `command-output/05_auto_quant_run_tomac_mtf.err`

## Readback

- `03_prepare_external_direct.exit=0`.
- The direct external prepare loaded `260` rows from `profile_source.csv`, with `bad_date=0`, `duplicate_ts=0`, and `nan_ohlc=0`.
- Prepared range was `2025-10-31 16:00:00+00:00` to `2025-12-31 20:00:00+00:00`.
- It wrote local feathers for `B2R_NQ_COST_CRISIS_REPAIR_032157/USD`: `260` bars at `1h`, `260` bars at `4h`, and `53` bars at `1d`.
- `04_auto_quant_status_after_direct_prepare.exit=0` and reported `status=dependency_ready_data_ready`, `healthy=true`, `dependency_healthy=true`, and `data_ready=true`.
- `05_auto_quant_run_tomac_mtf.exit=1`.
- `05_auto_quant_run_tomac_mtf.out` reported `TomacNQ_KillzoneBreakout` with `status=ERROR`, `error_type=OperationalException`, and `error_msg=No pair in whitelist.`

## Gate

- `diagnostic_only:agent_selected_mtf_data_ready`.
- `fail_closed:agent_selected_mtf_tomac_no_pair_in_whitelist`.
- `blocked:user_selected_historical_data_missing`.
- `not_started:no_mature_rooted_observations_no_downstream_promotion_rerun`.
- `promotion_allowed=false`.

## Next

Do not promote from the prepared MTF workspace or the failed Tomac run. The next qualifying Board B move still requires explicit user selection of `HTF`, `MTF`, or `LTF`. If the selected path uses this Auto-Quant/Freqtrade shape, repair the synthetic pair whitelist before relying on any backtest output, and carry forward only nonzero mature rooted branch observations through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
