# Auto-Quant Isolated Seeded BTC Run v1

Run id: `20260512T023540-codex-autoquant-isolated-seeded-btc-run-v1`
Gate result: `autoquant_isolated_seeded_btc_run_v1=seeded_btc_strategy_backtests_succeeded_non_promoting_source_control_blocked`
Board sha256 at generation: `85f13c62a42d509a3c0bbef781545fe460352e7b9f654aec46a3497d96c133c6`

Scope:
- Used the already data-ready 022826 isolated Auto-Quant workspace under `/tmp`.
- Seeded three active BTC-only wrapper strategies into that isolated workspace only.
- Ran Auto-Quant `run.py`; no source/control roots, canonical intake, or repo runtime code were mutated.

Seeded wrappers:
- `BTCLeaderBreakV4BTCOnly.py` sha256 `0f44c5562419ed0e2ac9d81a1092167916b559906ec865b99c7dc1efbf3c9f56`.
- `MTFTrendStackBTCOnly.py` sha256 `3846d6f8de215c2a62e51ccb0a88ffecf24cc57c0aa260b533c577d1d9ae1e57`.
- `MomentumMTFConfluenceBTCOnly.py` sha256 `f0e2ab4afeaae6d3e8f2152672e036b386799f3905e7205917caa299231246f6`.

Command result:
- Command: `uv run --with ta-lib run.py`.
- Exit: `0`.
- Done line: succeeded `3`, failed `0`.

Strategy results:
- `BTCLeaderBreakV4BTCOnly` pair basket `BTC/USDT` trades `116` profit `14.8100%` Sharpe `0.2464` win rate `35.3448%` PF `2.3460`.
- `MTFTrendStackBTCOnly` pair basket `BTC/USDT` trades `150` profit `-4.2700%` Sharpe `-0.0796` win rate `22.0000%` PF `0.8513`.
- `MomentumMTFConfluenceBTCOnly` pair basket `BTC/USDT` trades `169` profit `2.8600%` Sharpe `0.0411` win rate `30.7692%` PF `1.0709`.

Robust summaries:
- `BTCLeaderBreakV4BTCOnly` robust_sharpe `0.2464   # min across declared timeranges`.
- `MTFTrendStackBTCOnly` robust_sharpe `-0.0796   # min across declared timeranges`.
- `MomentumMTFConfluenceBTCOnly` robust_sharpe `0.0411   # min across declared timeranges`.

Decision:
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- `update_goal=false`.

Why non-promoting:
- This is isolated Auto-Quant runtime/backtest evidence only.
- It does not provide source-owned `MainRegimeV2` labels, R6 owner/control rows, explicit `FLIP` approval, per-regime qualifying conditions, cross-market/cycle validation, or canonical merge.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T023540-codex-autoquant-isolated-seeded-btc-run-v1/autoquant-isolated-seeded-btc-run-v1/autoquant_isolated_seeded_btc_run_v1.json`.
- Metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T023540-codex-autoquant-isolated-seeded-btc-run-v1/autoquant-isolated-seeded-btc-run-v1/autoquant_isolated_seeded_btc_metrics_v1.csv`.
- Wrapper CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T023540-codex-autoquant-isolated-seeded-btc-run-v1/autoquant-isolated-seeded-btc-run-v1/seeded_strategy_wrappers_v1.csv`.
- Command stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T023540-codex-autoquant-isolated-seeded-btc-run-v1/command-output/autoquant_seeded_run.stdout.txt`.
- Command stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T023540-codex-autoquant-isolated-seeded-btc-run-v1/command-output/autoquant_seeded_run.stderr.txt`.
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T023540-codex-autoquant-isolated-seeded-btc-run-v1/checks/autoquant_isolated_seeded_btc_run_v1_assertions.out`.

Next:
- Preserve the Current Cursor next action for R6. Continue from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream promotion.
