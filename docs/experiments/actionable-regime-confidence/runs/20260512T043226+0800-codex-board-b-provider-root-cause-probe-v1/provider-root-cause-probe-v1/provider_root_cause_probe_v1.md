# Board B Provider Root-Cause Probe v1

Run id: `20260512T043226+0800-codex-board-b-provider-root-cause-probe-v1`

Scope: read-only provider readiness diagnosis for the Board B `034002` fail-closed cursor. This probe does not select historical data, does not run selected-data factor-research, does not create profitability evidence, and does not call `update_goal`.

## Objective Mapping

- Required providers: IBKR, TradingViewRemix, yfinance, and Kraken are explicitly part of the objective.
- Current promotion gate: still blocked on explicit `user_selected_historical_data`.
- This probe only separates provider root causes so later selected-data work does not overclaim provider readiness or call the lane `data_blocked` from one failed path.

## Evidence

- `command-output/00_system_python_ibkr_import.{cmd,out,err,exit}`
- `command-output/01_uv_ibkr_import.{cmd,out,err,exit}`
- `command-output/02_system_python_public_import.{cmd,out,err,exit}`
- `command-output/03_uv_public_import.{cmd,out,err,exit}`
- `command-output/04_tvremix_tools_list_direct.{cmd,out,err,exit}`
- `command-output/05_uv_ibkr_import_retry_warm_cache.{cmd,out,err,exit}`
- `docs/experiments/actionable-regime-confidence/runs/20260512T042613+0800-codex-board-b-provider-status-refresh-v1/provider_status_refresh_readback_v1.md`

## Readback

- `00_system_python_ibkr_import.exit=1`: system `python3` cannot import `redis`, so the repo `provider-status` IBKR failure is a real system-runtime dependency failure.
- `01_uv_ibkr_import.exit=2`: the first low-pollution `uv` IBKR probe failed while fetching `redis` from PyPI after retries; this was a transient fetch/cache issue, not proof that the package set is impossible.
- `05_uv_ibkr_import_retry_warm_cache.exit=0`: after the `/tmp/ict-engine-provider-deps-uv-cache` cache was warmed, `uv run --with redis --with ib_async --with pandas` imported `redis`, `ib_async`, and local `ibkr_bridge` successfully.
- `02_system_python_public_import.exit=1`: system `python3` cannot import `ccxt`, so the repo `provider-status` Kraken public failure is also a real system-runtime dependency failure.
- `03_uv_public_import.exit=0`: a non-persistent `uv` environment with `requests`, `pandas`, `ccxt`, `ib_async`, `redis`, `pyyaml`, `scikit-learn`, `pyarrow`, and `xgboost` imports the public provider dependency set successfully.
- `04_tvremix_tools_list_direct.exit=1`: local `~/.ict-engine/tvremix_mcp.json` exists and credentials were used, but the direct `tools/list` probe returned HTTP `429` with `Rate limit exceeded. Retry after 12183s`; this is a remote rate-limit/connectivity blocker, not a missing local config file.

## Root Cause Classification

- IBKR market-data blocker: system Python dependency environment is missing `redis`; low-pollution `uv` can satisfy the import set, and the local gateway is separately reported reachable on port `4002`.
- Kraken public blocker: system Python dependency environment is missing `ccxt`; low-pollution `uv` can satisfy the full public fetch import set.
- TradingViewRemix blocker: credentials/config file are present, but the remote MCP endpoint is rate-limited for `tools/list`.
- yfinance/Kraken CLI status from `042613` remains ready and unchanged.

## Gate

- `diagnostic_only:provider_root_cause_probe`.
- `pass:uv_ibkr_import_set_ready_after_cache_warm`.
- `pass:uv_public_provider_import_set_ready`.
- `fail_closed:system_python_ibkr_missing_redis`.
- `fail_closed:system_python_public_missing_ccxt`.
- `fail_closed:tradingview_mcp_rate_limited_429_retry_after_12183s`.
- `blocked:user_selected_historical_data_missing`.
- `provider_profitability_evidence=false`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

- For IBKR and Kraken public, prefer low-pollution `uv` wrappers for ad-hoc provider fetches instead of mutating system Python.
- For TradingViewRemix, do not retry aggressively until the reported rate-limit window has passed or the user refreshes credentials/endpoint.
- Keep `034002` fail-closed. The next qualifying Board B action still requires explicit user selection of exactly one of `HTF=1d`, `MTF=4h`, or `LTF=1h`, then selected-data factor-research/Auto-Quant and downstream continuation only if nonzero mature rooted branch observations exist.
