# 115700 Selected-History Factor Research v1

Run id: `20260512T122600+0800-codex-115700-selected-history-factor-research-v1`
Source downstream line: `20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`
Source provider/AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`

## Result
- `factor-research` before prepare exited `0` and produced an Auto-Quant handoff, but data was not ready.
- `auto-quant-prepare` exited `0`; the workspace became `dependency_ready_data_ready`.
- `factor-research` after prepare exited `0` and pointed to `run_tomac.py` with `3` active external TOMAC strategies.
- First TOMAC invocation from the repo root exited `1`: `ModuleNotFoundError: No module named 'freqtrade'`.
- Workspace-scoped TOMAC invocation exited `1`: Freqtrade dropped the long synthetic pair `B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700/USD` from the whitelist.
- Short-pair repair was applied only inside this experiment workspace: config pair `B2R115700/USD`, with matching copied data files `B2R115700_USD-{1h,4h,1d}.feather`.
- The next TOMAC run exited `1` because config timerange `20230101-20251231` excluded the actual selected-history data that starts `2026-04-01`.
- Timerange repair was applied only inside this experiment workspace: `20260401-20260512`.
- Final TOMAC run exited `0`: all `3` strategies ran, `0` failed, but every strategy produced `0` trades.

## Measured Strategy Readback

| strategy | exit | trades | sharpe | total_profit_pct | win_rate_pct | status |
|---|---:|---:|---:|---:|---:|---|
| `TomacAggressiveBE` | `0` | `0` | `0.0000` | `0.0000` | `0.0000` | no candidate |
| `TomacKillzoneBreakout` | `0` | `0` | `0.0000` | `0.0000` | `0.0000` | no candidate |
| `TomacRRWinRate` | `0` | `0` | `0.0000` | `0.0000` | `0.0000` | no candidate |

## Decision
- Gate: `115700_selected_history_factor_research_v1=auto_quant_prepared_and_tomac_ran_but_zero_trades_no_downstream_promotion`.
- This is real Auto-Quant execution evidence, but it is not a usable strategy packet.
- No Auto-Quant trade rows were produced, so there is nothing new to ingest into Pre-Bayes, BBN, CatBoost/path-ranker, or the execution tree from this run.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- Handoff before prepare: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1/command-output/factor_research_selected_history.out`
- Prepare output: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1/command-output/auto_quant_prepare.out`
- Handoff after prepare: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1/command-output/factor_research_after_prepare.out`
- Failed repo-root TOMAC run: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1/command-output/run_tomac_selected_history.err`
- Failed long-pair TOMAC run: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1/command-output/run_tomac_selected_history_workspace.out`
- Failed pre-timerange TOMAC run: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1/command-output/run_tomac_selected_history_shortpair.out`
- Final TOMAC run: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1/command-output/run_tomac_selected_history_shortpair_timerange.out`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1/checks/115700_selected_history_factor_research_v1_assertions.out`

## Next
- Do not promote this run.
- The next useful action is either to iterate strategy logic inside the isolated Auto-Quant workspace until nonzero trade rows exist, or use `122351` evidence-node candidates on non-BTC / non-1h contexts before another downstream chain claim.
