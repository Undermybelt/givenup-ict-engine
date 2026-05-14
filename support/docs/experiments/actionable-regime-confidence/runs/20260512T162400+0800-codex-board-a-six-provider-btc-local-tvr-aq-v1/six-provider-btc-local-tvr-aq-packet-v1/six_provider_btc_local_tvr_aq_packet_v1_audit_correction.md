# 162400 Provider/AQ Audit Correction

This correction audits the existing `162400` provider/AQ packet without rerunning provider fetches, Auto-Quant, or downstream ict-engine commands.

## Corrected Readback

- Provider material is present under the `162400` root for all six required rows: yfinance/YF, Kraken, Binance, Bybit, TradingViewRemix/TVR local stdio, and IBKR PAXOS AGGTRADES.
- Auto-Quant compile and `run_tomac` command artifacts are present under the `162400` root and exited `0` for all six provider labels.
- The AQ helper consumed `162400` provider CSV paths, but the Freqtrade workspace paths recorded in JSON/stdout point to the older `20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/workspace/...` root.
- Therefore `same_root_six_provider_aq_authority=True` in the generated report is too strong for strict Board A accounting. A more precise reading is `provider_material_consumed=true`, `aq_workspace_same_root=false`, and `strict_same_root_aq_authority=partial`.
- The requested provider window was hard-coded around `2026-04-01` to `2026-05-12`, with returned provider rows of roughly `720` to `985` in the final AQ packet. This is short-window evidence, not the large-window factor-training evidence the user requested.
- AQ metrics are low-sample per provider/strategy: momentum trades range from `10` to `37`, pullback trades range from `6` to `17`, and several provider/strategy metrics are negative.
- Total AQ trades across all strategies/providers are `224`, but this aggregation does not establish a factor family or calibrated regime-confidence packet.
- No filter/Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree admission artifact is present under this root.

## Gate

- `provider_rows_current_same_root=6/6`.
- `aq_commands_exited_0=6/6`.
- `provider_material_consumed=true`.
- `aq_workspace_same_root=false`.
- `strict_same_root_aq_authority=partial`.
- `sample_adequacy=smoke_only`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not promote or downstream-promote `162400` as accepted Board A evidence. The next useful repair is a fresh provider/AQ packet or repair slice that keeps AQ workspaces under the active run root, requests the maximum feasible provider-backed history for the selected timeframe, reports requested-vs-returned windows, and only then carries adequate evidence through filter/Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree.
