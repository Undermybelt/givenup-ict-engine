# AutoQuant Bootstrap Prepare Readback After 032145 v1

Run id: `20260512T032658-codex-autoquant-bootstrap-prepare-readback-after-032145-v1`

Gate result: `autoquant_bootstrap_prepare_readback_after_032145_v1=bootstrap_succeeded_prepare_failed_dns_source_controls_absent_no_promotion`

Board sha256 before artifact: `61efeca4302f41e5c3df225433db6ee61d9ebe682668b56ec3d50431cdf2a68b`

## Scope

This packet follows up the `032145` provider/Auto-Quant readiness refresh by actually operating the Auto-Quant bootstrap and prepare path in the isolated `/tmp` state. It records diagnostics only. It does not mutate source roots, accept labels, acquire owner controls, approve `FLIP` rows, relax thresholds, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Command Readback

- Baseline `032145` Auto-Quant status command exited `0` and reported `missing_dependency`, `bootstrap_needed=true`, `dependency_healthy=false`, and `data_ready=false`.
- Ran `./target/debug/ict-engine auto-quant-bootstrap --state-dir /tmp/ict-engine-board-a-readonly-refresh-20260512T032145/auto-quant`; it exited `0`, cloned/pinned Auto-Quant at `34ba6b6ee6aa69813a50a72158d4c089d97afb96`, and reported dependency health `true`.
- Re-running status against the original outer state still reported `missing_dependency`; diagnosis is CLI state-dir recursion: the shell wrapper maps `--state-dir` to `<state-dir>/auto-quant`, while the readiness follow-up command already used the mapped Auto-Quant state path.
- Using `ICT_ENGINE_AUTO_QUANT_OUTPUT_DIR=/tmp/ict-engine-board-a-readonly-refresh-20260512T032145/auto-quant/auto-quant` made status target the bootstrapped dependency and report `dependency_ready_data_missing`, `dependency_healthy=true`, and `data_ready=false`.
- Ran `auto-quant-prepare` with the same output-dir override. It exited `1`: Freqtrade/CCXT could not load Binance markets because DNS failed for `api.binance.com`, then `prepare.py` stopped with `Markets were not loaded`.
- Post-prepare status remains `dependency_ready_data_missing`.

## Runtime Context

- Provider readiness from `032145`: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Durable provider paths remain yfinance ready and `kraken_cli` ready; IBKR/IBKR bridge and TradingView MCP remain configured but unhealthy.
- Pre-Bayes in the isolated state has no latest gate, filtered assignments, policy version, structural feedback, or soft evidence.
- Workflow status remains fail-closed with `blocking_truth.status=insufficient_state`, no promotable artifact, and `actionable_artifacts=0`.

## Decision

- Auto-Quant dependency bootstrap: `succeeded`.
- Auto-Quant data prepare: `failed_dns_binance_markets_not_loaded`.
- CLI state-dir recursion observed: `true`, diagnostic only; runtime code changed `false`.
- R6 owner-export root, R3 native-subhour source-label root, and R5 recency-extension root remain absent.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Preserve the Current Cursor next action. Source/control gates still dominate: acquire verifier-native owner/operator rows and matched controls, or record explicit `FLIP` approval/source-owned controls. Treat this Auto-Quant packet as dependency diagnostics only; do not promote bootstrap success or failed Binance data preparation into Board A acceptance.
