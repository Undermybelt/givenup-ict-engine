# Agent-Selected LTF Auto-Quant Readback v1

This is an additive, non-promoting readback for the existing `035139` sidecar. It does not edit the Current Cursor and does not satisfy `user_selected_historical_data`.

## Result

- `05_prepare_external_nq_ltf`: exit `0`; generated `NQ_USD-1h`, `NQ_USD-4h`, `NQ_USD-1d` feathers from `analyze_nq_ltf.json`.
- `06_py_compile_tomac_adapter_and_strategies`: exit `0`.
- `07_auto_quant_run_tomac_nq_ltf`: exit `1`; failed before strategy logic because generated feather timestamps were epoch seconds.
- `08_fix_nq_feather_epoch_ms`: exit `0`; converted generated NQ feather dates to epoch milliseconds.
- `09_auto_quant_run_tomac_nq_ltf_epoch_fixed`: exit `0`; FreqTrade loaded NQ data, but all three strategies produced `0` trades.

| Strategy | Trades | Sharpe | Profit % | Win % | Profit Factor |
|---|---:|---:|---:|---:|---:|
| `NqLtfExpansionBreakout` | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `NqLtfRangeSnapback` | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `NqLtfSweepReclaim` | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Gate

Fail-closed: there are no mature LTF branch observations to send through Pre-Bayes, BBN, CatBoost/path-ranker, or execution tree. Promotion remains blocked by the existing `034002/downstream-combined-v1` gates.

## Evidence

- `command-output/05_prepare_external_nq_ltf.out`
- `command-output/08_fix_nq_feather_epoch_ms.out`
- `command-output/09_auto_quant_run_tomac_nq_ltf_epoch_fixed.out`
- `agent-selected-ltf-v1/agent_selected_ltf_autoquant_readback_v1.json`
