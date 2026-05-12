# IBKR HMDS SPY Spotcheck v1

Run id: `20260512T111538+0800-codex-ibkr-hmds-spy-spotcheck-v1`

This is a provider-health spot-check only. It does not count as Board A source/control evidence, Board B provider-matrix AQ evidence, selected-history approval, canonical merge input, downstream promotion evidence, live trade evidence, completion, or `update_goal` authorization.

Readback:
- Local consent and capabilities files are present under `~/.ict-engine/`.
- `127.0.0.1:4002` is reachable.
- Repo provider-status still reports `ibkr` and `ibkr_bridge` as not ready because the repo runtime lacks required IBKR dependencies, even though the local gateway is reachable.
- A direct low-pollution `uv run --with ib_async --with pandas` probe connected to local IB Gateway, qualified `SPY`, requested `2 D` of `1 day` `TRADES` history, and returned `2` bars from `2026-05-08` through `2026-05-11`.
- IBKR API messages included `2107` inactive/on-demand for `apachmds` and `ushmds`, then `2106` historical data farm OK for `ushmds` after the US historical request.
- Read-only API notices were observed; no order or account mutation was attempted.

Decision:
- `Inactive: apachmds, ushmds` is not a hard historical-data failure by itself. It is an on-demand farm state.
- It is also not a valid reason to skip IBKR in Board A or Board B provider matrices.
- For US historical data, `ushmds` activated and returned rows in this spot-check.
- `apachmds` remains unexercised because no APAC contract was requested.
- Promotion remains fail-closed: this spot-check is provider availability context, not provider-matrix AQ evidence and not source/control evidence.

Gate:
- `pass:local_ibkr_gateway_port_4002_reachable`.
- `pass:direct_uv_ib_async_spy_history_returned_2_rows`.
- `pass:ushmds_activated_on_demand_after_us_request`.
- `partial:apachmds_inactive_no_apac_contract_requested`.
- `fail_closed:repo_provider_status_ibkr_runtime_dependencies_missing`.
- `fail_closed:not_board_a_source_control_evidence`.
- `fail_closed:not_board_b_six_provider_aq_authority`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
