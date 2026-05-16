# Provider Runtime 8/8 Repair

Decision: handoff, provider-status repair verified.

Scope:
- Identify the remaining `market_data:7/8 ready` blocker.
- Repair local shell/provider runtime defaults without touching active Board A/B branches.
- Commit only this compact evidence packet; shell dotfile changes live outside this repository.

Remaining blocker:
- `hubble`
- prior status: `installed_unconfigured`
- prior reason: `hubble_base_url_missing`

Repair applied outside repo:
- `/Users/thrill3r/.zprofile`: re-prepends `$HOME/.local/bin` after Homebrew shellenv so zsh uses Python 3.13 provider deps instead of Homebrew python@3.14.
- `/Users/thrill3r/.zshenv`: exports local TradingView MCP stdio settings:
  - `ICT_ENGINE_TRADINGVIEW_MCP_CMD=uv`
  - `ICT_ENGINE_TRADINGVIEW_MCP_ARGS=--directory $HOME/tradingview-mcp/tradingview-mcp run tradingview-mcp`
- `/Users/thrill3r/.zshenv`: exports Hubble V2 base URL:
  - `ICT_ENGINE_HUBBLE_BASE_URL=http://43.167.234.49:3101`

Verification:
- `checks/provider_status_compact.txt`: `market_data:8/8 ready`.
- `checks/provider_status_hubble_agent.json`: `hubble` ready, reason `hubble_base_url_env_configured_with_upstream_default_key`.
- `checks/provider_status_ibkr_agent.json`: `ibkr` ready, reason `local_ibkr_runtime_ready`.
- `checks/provider_status_tradingview_mcp_agent.json`: `tradingview_mcp` ready/degraded for OHLCV, reason `local_stdio_ohlcv_ready_options_unverified`.

Caveat:
- Hubble provider-status readiness is env/config readiness. A direct curl smoke to the public Hubble endpoint returned an empty reply during this repair window, so provider-status is green but downstream Hubble fetches still need per-request validation before using data as evidence.
