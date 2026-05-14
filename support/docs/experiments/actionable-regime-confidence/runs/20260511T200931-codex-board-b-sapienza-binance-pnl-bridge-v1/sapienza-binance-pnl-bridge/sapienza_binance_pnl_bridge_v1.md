# Sapienza Binance PnL Bridge v1

Run ID: `20260511T200931+0800-codex-board-b-sapienza-binance-pnl-bridge-v1`

## Decision

- Gate result: `fail:insufficient_positive_rows`
- PnL rows: `480`
- Attached positive events: `24`
- Attached control events: `72`
- Current Binance-mapped source symbols: `13/85`
- Best horizon: `6h`
- Best edge vs controls: `-0.012033`
- Best edge LCB 5%: `-0.033142`
- Best fold positive rate: `0.058824`
- Downstream consumption: `not_started:diagnostic_only_full_board_b_still_requires_all_root_rc_spa`
- Promotion allowed: `False`

## Interpretation

- This is a source/family switch from the failed Mehrnoom horizon sweep to the accepted Sapienza pump/dump positive-control source.
- It uses source-owned labels for event/control identity and Binance public 1h candles for provider-reconstructed entry/exit PnL.
- It remains fail-closed for full Board B because Bull/Bear/Sideways/Crisis root branches still have not passed the five-root RC-SPA gate, and no downstream Pre-Bayes/BBN/CatBoost/execution-tree promotion was started.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T200931-codex-board-b-sapienza-binance-pnl-bridge-v1/sapienza-binance-pnl-bridge/sapienza_binance_pnl_bridge_v1.json`
- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T200931-codex-board-b-sapienza-binance-pnl-bridge-v1/sapienza-binance-pnl-bridge/sapienza_binance_pnl_rows_v1.csv`
- Horizon summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T200931-codex-board-b-sapienza-binance-pnl-bridge-v1/sapienza-binance-pnl-bridge/sapienza_binance_horizon_summary_v1.csv`
- Symbol coverage CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T200931-codex-board-b-sapienza-binance-pnl-bridge-v1/sapienza-binance-pnl-bridge/sapienza_binance_symbol_coverage_v1.csv`
- Provider probe JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T200931-codex-board-b-sapienza-binance-pnl-bridge-v1/sapienza-binance-pnl-bridge/sapienza_binance_provider_probe_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T200931-codex-board-b-sapienza-binance-pnl-bridge-v1/checks/sapienza_binance_pnl_bridge_v1_assertions.out`
