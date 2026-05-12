# Offline v041 Closeout v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T092520+0800-codex-board-b-aq-first-nursery-feedback-after-091850-v1`

Command:
- `uv run run_offline_v041.py`
- Exit: `0`

Evidence files:
- Command: `command-output/04_auto_quant_run_v041_offline.cmd`
- Exit: `command-output/04_auto_quant_run_v041_offline.exit`
- Stdout: `command-output/04_auto_quant_run_v041_offline.out`
- Stderr: `command-output/04_auto_quant_run_v041_offline.err`

Readback:
- The offline v0.4.1 run used the run-local Auto-Quant workspace and synthetic market shim.
- Data existed locally for `BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `BNB/USDT`, and `AVAX/USDT` at `1h`, `4h`, and `1d`.
- Strategies evaluated: `CrashRebound`, `PerPairMR`, and `RegimeAdaptiveBNB`.
- The run produced `12` successful backtests and `0` failures.

Compact metrics:
- `CrashRebound`: `bull_2021`, `winter_2022`, `recovery_23_25`, and `full_5y` all had positive total profit. Summary robust Sharpe was `0.1516`; worst profit was `8.6300%`; full 5y had `176` trades, `40.5800%` total profit, `65.3409%` win rate, `1.4204` profit factor, and `-11.5829%` max drawdown. Profit floor failed because not every timerange cleared the `20.0%` threshold.
- `PerPairMR`: summary robust Sharpe was `-0.2159`; worst profit was `-2.4800%`; full 5y had `287` trades, `23.9700%` total profit, `64.1115%` win rate, `1.3191` profit factor, and `-10.8912%` max drawdown. Profit floor failed.
- `RegimeAdaptiveBNB`: summary robust Sharpe was `-0.0390`; worst profit was `-0.7600%`; full 5y had `30` trades, `15.9600%` total profit, `60.0000%` win rate, `2.2702` profit factor, and `-6.6142%` max drawdown. Profit floor failed.

Decision:
- This is real nonzero Auto-Quant/Freqtrade nursery evidence, but it remains `incubation_only`.
- It does not satisfy Board A source/control evidence, explicit selected-history approval, selected-data AutoQuant promotion, downstream Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion, trade usability, or `update_goal`.
- The useful signal is that `092520` is no longer only a DNS-failure root; its later offline v0.4.1 path produced measurable non-promoting crypto nursery feedback.
