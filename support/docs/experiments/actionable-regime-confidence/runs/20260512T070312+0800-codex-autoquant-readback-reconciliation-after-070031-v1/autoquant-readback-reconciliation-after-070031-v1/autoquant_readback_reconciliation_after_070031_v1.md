# AutoQuant Readback Reconciliation After 070031 v1

Run id: `20260512T070312+0800-codex-autoquant-readback-reconciliation-after-070031-v1`

Gate result: `autoquant_readback_reconciliation_after_070031_v1=tomac_success_registered_runtime_only_source_control_unlock_absent_no_promotion`

## Scope

This reconciliation resolves ordering drift between the `070031` failed-run consolidation and the settled `065613` Tomac-specific command output registered by `070059`. It does not rerun Auto-Quant, mutate source roots, run canonical merge, run filter / Pre-Bayes / BBN / CatBoost / execution-tree promotion, make a trade claim, or call `update_goal`.

## Reconciled Decision

- Keep the `070031` failed-run readback for the default `run.py` paths: normal `065613`, threaded-resolver `065613`, and `065824` all failed at Freqtrade/Binance market loading.
- Add the `070059` Tomac-specific result to the settled accounting: `run_tomac.py` exited `0` with one local `TomacNQ_KillzoneBreakout` backtest on `QQQ/USD`, `74` trades, `52.7027%` win rate, `6.98%` total profit, `Sharpe 0.2207`, and `Profit factor 1.2501`.
- Reconciled runtime count: default/managed run success `0`, Tomac-specific local backtest success `1`.
- Promotion status is unchanged: the Tomac result is single-pair strategy output, not Board A source/control evidence, not per-regime `MainRegimeV2` confidence calibration, not R5/R3 verifier-native labels, not R6 owner/export controls, and not a post-unlock downstream chain run.

Accounting: accepted rows added `0`, valid required-root unlock false, source/control evidence acquired false, canonical merge false, provider/AutoQuant promotion false, filter / Pre-Bayes / BBN / CatBoost / execution-tree promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- `070031` failed-run consolidation: `docs/experiments/actionable-regime-confidence/runs/20260512T070031+0800-codex-autoquant-run-readback-after-data-ready-v1/autoquant-run-readback-after-data-ready-v1/autoquant_run_readback_after_data_ready_v1.md`
- `070059` Tomac settlement: `docs/experiments/actionable-regime-confidence/runs/20260512T070059+0800-codex-autoquant-local-cache-tomac-settlement-after-065613-v1/autoquant-local-cache-tomac-settlement-after-065613-v1/autoquant_local_cache_tomac_settlement_after_065613_v1.md`
- Reconciliation JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T070312+0800-codex-autoquant-readback-reconciliation-after-070031-v1/autoquant-readback-reconciliation-after-070031-v1/autoquant_readback_reconciliation_after_070031_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T070312+0800-codex-autoquant-readback-reconciliation-after-070031-v1/checks/autoquant_readback_reconciliation_after_070031_v1_assertions.out`

## Next

Keep Auto-Quant runtime evidence separated from Board A promotion evidence. Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 post-`2026-01-30` rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant promotion, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
