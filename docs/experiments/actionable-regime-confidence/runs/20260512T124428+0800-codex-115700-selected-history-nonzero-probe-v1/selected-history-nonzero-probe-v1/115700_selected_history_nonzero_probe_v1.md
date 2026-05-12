# 115700 Selected-History Nonzero Probe v1

Run id: `20260512T124428+0800-codex-115700-selected-history-nonzero-probe-v1`

This is an isolated diagnostic probe after the `122600` pair repair readback. It reuses the existing selected-history data and sanitized selected-window config, but keeps the probe strategies in this run root. It does not modify `ict-engine` runtime code and does not modify the existing `122600` Auto-Quant workspace.

## Objective

Test whether the selected-history Freqtrade harness can produce nonzero closed trades after pair construction was repaired.

## Commands

- Probe-only command output: `command-output/run_nonzero_probe.out`
- Probe-only stderr: `command-output/run_nonzero_probe.err`
- Probe + always-in control output: `command-output/run_nonzero_probe_with_control.out`
- Probe + always-in control stderr: `command-output/run_nonzero_probe_with_control.err`

## Readback

The first diagnostic strategy, `B2R115700SelectedHistoryMomentumProbeV1`, exited `0` and succeeded under Freqtrade, but produced:

- `trade_count=0`
- `total_profit_pct=0.0000`
- `win_rate_pct=0.0000`
- `profit_factor=0.0000`

An offline pandas check against `B2RSAMEROOTSIXPROVIDER1HAQ115700_USD-1h.feather` showed the momentum condition itself was not empty:

- momentum condition rows: `184`
- after startup 30: `182`
- with nonzero volume: `83`

The second diagnostic strategy, `B2R115700AlwaysInControlProbeV1`, forced `enter_long=1` on all available rows and used zero-threshold ROI as a harness control. It also exited `0` and succeeded under Freqtrade, but still produced:

- `trade_count=0`
- `total_profit_pct=0.0000`
- `win_rate_pct=0.0000`
- `profit_factor=0.0000`

This means the current selected-history blocker is not only "TOMAC thresholds are too selective." Even a control recipe did not produce closed trades in this harness.

## Gate

- `support_once:124428_115700_selected_history_nonzero_probe_v1`
- `supporting_only:nonzero_trade_probe_after_pair_repair`
- `pass:commands_exit0`
- `pass:manual_momentum_signal_rows_184`
- `fail_closed:momentum_probe_trade_count_0`
- `fail_closed:always_in_control_trade_count_0`
- `fail_closed:nonzero_trade_recipe_found_false`
- `fail_closed:no_measured_profitability_packet`
- `fail_closed:no_rc_spa_surface`
- `fail_closed:no_downstream_promotion_artifact`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Do not spend more loops on stricter selected-history strategies in this `122600` harness. The next valid work is to diagnose why even the always-in control strategy produces zero closed trades, or use a wider provider-provenanced history/harness that can create nonzero selected-history observations before RC-SPA and downstream closure.
