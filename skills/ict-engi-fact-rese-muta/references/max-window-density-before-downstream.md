# Max-window density before downstream

Use when the user asks to keep training profitable factors from a 1m origin with the widest feasible window and full MTF coverage.

## Durable lesson

If a regime-rooted profitability branch is sparse, do not add more overlays or push it through BBN/CatBoost/execution-tree just because some higher-timeframe siblings look positive. First expand each real provider lane to the maximum feasible window, then choose a denser 1m-origin entry family.

## Required shape

- Branch root must remain: `market -> product -> symbol -> timeframe -> main_regime -> sub_regime -> candidate/profit_factor`.
- Run real available frames: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`.
- If a frame is provider-unsupported or absent (often `4h`), mark it missing; do not synthesize it.
- Inspect `auto_quant_agent_material_rank*.json` `ranking[]` directly; summary helper counters can be stale.
- Judge per-timeframe terminal decisions first, then ladder summary.

## Gate rule

Proceed downstream only if the exact 1m-origin rooted branch has enough real trades and does not become negative after cost stress. Positive `30m`/`1h` siblings are context or confirmation, not promotion evidence for a failed `1m` origin.

## Common terminal classifications

- `keep_subclass_evidence_or_drop_gate1_no_downstream`: 1m sparse/negative, some HTF positives.
- `sparse_density_retry_max_window`: window not yet maximized; retry wider real lanes before verdict.
- `drop_compound_overlay`: overlay reduced trade count or expectancy versus base factor.
- `missing_timeframe_provider`: requested frame absent from provider; record and continue real lanes.

## Practical next step

Prefer denser 1m families such as session VWAP/noise-band, ORB/RVOL, reclaim, or time-of-day slot alpha only if they survive the same Auto-Quant Gate 1, cost stress, provider-parity, and downstream exact-branch checks.