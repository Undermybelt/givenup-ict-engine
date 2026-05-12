# AutoQuant Final Readback After 065824 v1

Run id: `20260512T070115+0800-codex-autoquant-final-readback-after-065824-v1`

Gate result: `autoquant_final_readback_after_065824_v1=tomac_runtime_ok_no_source_control_unlock_no_downstream`

Board sha256 before artifact: `af1d64f37c9503ef8e10817bedb5b752d08e2bf6a02e5935a2a57fc016433c42`

## Scope

This readback consolidates the late `065613`, `065652`, and `065824` Auto-Quant artifacts after the local-cache and threaded-resolver attempts settled. It does not mutate R3/R5/R6 source roots, approve TSIE, materialize public candidates into target roots, run direct verifier, run split calibration, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Evidence

- `065613` local cache bootstrap, rsync, prepare, and status all exited `0`; status reported `dependency_ready_data_ready`, `healthy=true`, and `data_ready=true` for `/tmp/ict-engine-board-a-autoquant-local-cache-data-ready-065613-v1`.
- `065613` default Auto-Quant run discovered `3` strategies (`CrashRebound`, `PerPairMR`, `RegimeAdaptiveBNB`) but exited `1`; all `12` attempted backtests failed on Freqtrade/Binance market loading.
- `065613` threaded-resolver retry also exited `1`; all `12` attempted backtests still failed on Freqtrade/Binance market loading.
- `065824` readback confirmed `/tmp/ict-engine-board-a-064259-runtime-v1` status was `dependency_ready_data_ready`; the same state had one active default strategy file, `TomacNQ_KillzoneBreakout.py`.
- `065824` direct run against the `064259` state exited `1`; `TomacNQ_KillzoneBreakout` failed on Freqtrade/Binance market loading.
- A settled `065613` Tomac harness run exited `0` and backtested `TomacNQ_KillzoneBreakout` on `QQQ/USD` with `74` trades, `52.7027%` win rate, `6.98%` total profit, `Sharpe 0.2207`, `Profit factor 1.2501`, and max drawdown `-4.2049%`.

## Decision

The Auto-Quant runtime is demonstrably usable through the local Tomac harness, but this is runtime/backtest evidence only. It is not Board A acceptance evidence because R6 owner/export controls are still absent, R5 recency root is still absent, and R3 native-subhour evidence remains TSIE-quarantined and Crisis-absent.

Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; direct verifier run false; split calibration run false; canonical merge false; provider/AutoQuant promotion false; filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- `065613` root: `docs/experiments/actionable-regime-confidence/runs/20260512T065613+0800-codex-autoquant-local-cache-data-ready-after-065116-v1/command-output/`
- `065652` root: `docs/experiments/actionable-regime-confidence/runs/20260512T065652+0800-codex-autoquant-threaded-dns-prepare-after-065116-v1/command-output/`
- `065824` root: `docs/experiments/actionable-regime-confidence/runs/20260512T065824+0800-codex-autoquant-local-run-readback-after-065116-v1/command-output/`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T070115+0800-codex-autoquant-final-readback-after-065824-v1/autoquant-final-readback-after-065824-v1/autoquant_final_readback_after_065824_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T070115+0800-codex-autoquant-final-readback-after-065824-v1/checks/autoquant_final_readback_after_065824_v1_assertions.out`

## Next

Continue source/control acquisition only. Do not use the Tomac runtime pass as promotion evidence. A promotion rerun still requires explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned R5 post-`2026-01-30` rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.
