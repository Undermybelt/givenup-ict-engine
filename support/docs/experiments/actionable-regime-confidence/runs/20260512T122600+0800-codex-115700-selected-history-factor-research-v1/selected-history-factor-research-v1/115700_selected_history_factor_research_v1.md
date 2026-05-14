# 115700 Selected-History Factor-Research Readback v1

Generated: 2026-05-12T12:33:52+0800

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1`

Board hash before registration: `ba82bbefdad34289a2884f032ee8cf3522c84a69c257ba12ceab6da93a14457c`

## Scope

This is a terminal readback for the already-created `122600` selected-history factor-research attempt. It records command outcomes only. It does not edit the Board B cursor, does not promote a candidate, does not make a live-trade claim, and does not call `update_goal`.

## Inputs

- Selected recorded dataset path used by the attempt: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/provider-data-json/BTC_USD-1h.json`
- Auto-Quant symbol: `B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700`
- Objective: `expansion_manipulation`
- Auto-Quant pinned commit: `b640cc8ea0fd3ac5e6b2eaca75ba8abbd0aca91f`

## Readback

- Initial `factor-research` exited `0` but reported `dependency_ready_data_missing`.
- `auto-quant-prepare` exited `0` and moved readiness to `dependency_ready_data_ready`.
- Prepared data files were present for `1h`, `4h`, and `1d` under the isolated Auto-Quant workspace.
- Post-prepare `factor-research` exited `0` and recommended `uv run --with ta-lib .../run_tomac.py`.
- Direct TOMAC invocation exited `1` with `ModuleNotFoundError: No module named 'freqtrade'`.
- Workspace-owned TOMAC invocation exited `1`; Freqtrade loaded, but all three strategies failed with `OperationalException: No pair in whitelist`.
- Failed strategies: `TomacAggressiveBE`, `TomacKillzoneBreakout`, and `TomacRRWinRate`.
- Result: `0` successful backtests and `3` failed backtests.
- No measured profitability packet, RC-SPA surface, mature rooted observation set, or downstream Pre-Bayes/BBN/CatBoost/execution-tree promotion artifact was produced.

## Gate

- `support_once:122600_115700_selected_history_factor_research_v1`.
- `supporting_only:selected_history_1h_attempt_terminal_readback`.
- `pass:auto_quant_prepare_exit0_data_ready_true`.
- `pass:factor_research_after_prepare_exit0`.
- `fail_closed:direct_tomac_missing_freqtrade`.
- `fail_closed:workspace_tomac_no_pair_in_whitelist`.
- `fail_closed:tomac_successful_backtests_0_of_3`.
- `fail_closed:no_measured_profitability_packet`.
- `fail_closed:no_rc_spa_no_downstream_promotion`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not treat `122600` as a source-control unlock or profitability pass. The next useful slice is a narrow Auto-Quant/Freqtrade pair-construction repair for the already-isolated selected-history workspace, or a rerun through a known-good local/offline pair mapping. Any later promotion still requires measured profitability, chronological/cross-context validation, and non-observe execution readiness/actionability through the ordered Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree chain.
