# Provider Root-Cause Probe Readback v1

Run id: `20260512T043226+0800-codex-board-b-provider-root-cause-probe-v1`

Scope: diagnostic-only provider dependency and TradingViewRemix connectivity readback for Board B. This does not edit the Current Cursor, does not select historical data, does not create selected-data profitability evidence, does not run downstream promotion checks, and does not call `update_goal`.

## Command Readback

| Step | Exit | Readback |
|---|---:|---|
| `00_system_python_ibkr_import` | 1 | System Python cannot import the IBKR dependency stack because `redis` is missing. |
| `01_uv_ibkr_import` | 2 | `uv run --with redis --with ib_async --with pandas` failed while fetching `redis` from PyPI after retries/timeouts. |
| `02_system_python_public_import` | 1 | System Python cannot import the public-provider dependency stack because `ccxt` is missing. |
| `03_uv_public_import` | 0 | Ephemeral `uv` dependency stack imported `requests`, `pandas`, `ccxt`, `ib_async`, `redis`, `yaml`, `sklearn`, `pyarrow`, and `xgboost` successfully. |
| `04_tvremix_tools_list_direct` | 1 | Direct TradingViewRemix MCP `tools/list` probe returned HTTP `429` with body prefix `Rate limit exceeded. Retry after 12183s.` |

## Gate

- `diagnostic_only:provider_root_cause_probe`.
- `pass:uv_public_provider_dependency_stack_imports`.
- `fail_closed:system_python_ibkr_dependencies_missing_redis`.
- `fail_closed:uv_ibkr_dependency_fetch_timeout`.
- `fail_closed:system_python_public_provider_dependencies_missing_ccxt`.
- `fail_closed:tradingview_mcp_rate_limited_429_retry_after_12183s`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Do not use this provider probe as profitability evidence. It only clarifies provider/runtime blockers. The next qualifying Board B move still requires explicit user selection of exactly one of `HTF=1d`, `MTF=4h`, or `LTF=1h`, followed by selected-data factor-research/Auto-Quant and downstream continuation only if nonzero mature rooted branch observations preserve the required regime branch path through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
