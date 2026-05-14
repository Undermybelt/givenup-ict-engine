# Board A Kraken Current-Window Repair v1

Run id: `20260512T171227+0800-codex-board-a-kraken-current-window-repair-v1`

This probe repairs only Kraken current-window feasibility. It does not run Auto-Quant or downstream ict-engine gates.

## Readback
- Kraken PF_XBTUSD 1h requested `2026-02-18_to_2026-05-12_current_window`.
- Exit `0`, rows `1993`, first `2026-02-18 00:00:00+00:00`, last `2026-05-12 00:00:00+00:00`, status `current_row_ready`.

## Gate
- kraken_current_window_status=current_row_ready.
- auto_quant_started=false.
- downstream_started=false.
- promotion_allowed=false.
- trade_usable=false.
- update_goal=false.
