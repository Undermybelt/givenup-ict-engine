# OB/FVG AQ Agent-Material Packet v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T160511+0800-codex-ob-fvg-aq-agent-material-packet-v1`
Source screen root: `docs/experiments/actionable-regime-confidence/runs/20260512T151907+0800-codex-ob-fvg-regime-branch-screen-v1`
Source AQ seed root: `docs/experiments/actionable-regime-confidence/runs/20260512T150855+0800-codex-145809-aq-material-seed-dispatch-v1`

Purpose: convert the best `151907` OB/FVG screen leaf into a real Auto-Quant agent-material packet while preserving Board B branch identity.

Branch path:
- `TrendTransition -> LowVolatility -> up_momentum -> order_block_pullback_v1`

Provider contract:
- Six provider rows are emitted in `summaries/provider_provenance_matrix.csv`.
- TVR is recorded as unreachable from `154536`; this builder does not make a new TVR call.
- Non-TVR rows use provider-backed replay files from `150855` and are therefore `local_cache_replay=true` until a future same-root provider acquisition rerun.

Gate:
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
