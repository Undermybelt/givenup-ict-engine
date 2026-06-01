# ict-engine provider runtime repair

Use when `provider-status --compact` shows provider-dependency false negatives, especially `ibkr_runtime_dependencies_missing_with_gateway_reachable` or `tradingview_mcp_connectivity_probe_failed` while local alternate runtimes exist.

## Pattern

1. Check the exact shell used by the operator, not only the current agent process:

```bash
zsh -lc 'which python3; python3 --version; python3 - <<"PY"
import importlib.util
for m in ["redis", "ib_async", "pandas"]:
    print(m, bool(importlib.util.find_spec(m)))
PY'
```

2. If Homebrew `python@3.14` shadows the working user Python, place the user shim after any `brew shellenv` in `~/.zprofile`:

```bash
# Keep user Python shims ahead of Homebrew python@3.14; ict-engine IBKR deps live there.
export PATH="$HOME/.local/bin:$PATH"
```

3. For TradingViewRemix / TVR, distinguish remote HTTP from local stdio. Remote `tvremix.xyz` may return 429 while local OHLCV is usable. Prefer local stdio for OHLCV:

```bash
export ICT_ENGINE_TRADINGVIEW_MCP_CMD="uv"
export ICT_ENGINE_TRADINGVIEW_MCP_ARGS="--directory $HOME/tradingview-mcp/tradingview-mcp run tradingview-mcp"
```

4. If `provider-status --compact` is still `market_data:7/8 ready`, identify the missing row with a focused provider readback:

```bash
.local-artifacts/cargo-target/debug/ict-engine provider-status --provider hubble --agent
```

For Hubble, `installed_unconfigured:hubble_base_url_missing` means the runtime only needs a base URL to clear provider-status. The installed Hubble skill pack commonly documents:

```bash
export ICT_ENGINE_HUBBLE_BASE_URL="http://43.167.234.49:3101"
# ICT_ENGINE_HUBBLE_API_KEY is optional; ict-engine falls back to the upstream-compatible default when unset.
```

5. Verify targeted providers and one real fetch:

```bash
.local-artifacts/cargo-target/debug/ict-engine provider-status --provider ibkr --agent
.local-artifacts/cargo-target/debug/ict-engine provider-status --provider tradingview_mcp --agent
.local-artifacts/cargo-target/debug/ict-engine provider-status --provider hubble --agent
.local-artifacts/cargo-target/debug/ict-engine provider-status --compact
.local-artifacts/cargo-target/debug/ict-engine market-data-harness \
  --action fetch --role primary \
  --provider primary=tradingview_mcp \
  --symbol-spec primary=NASDAQ:QQQ \
  --interval 1d
```

## Expected healthy readback

- `ibkr`: `ready=true`, `reason=local_ibkr_runtime_ready`.
- `tradingview_mcp`: `ready=true`, often `status=ready_degraded`, `reason=local_stdio_ohlcv_ready_options_unverified`.
- `hubble`: `ready=true`, `reason=hubble_base_url_env_configured_with_upstream_default_key` when only the base URL is set.
- `provider-status --compact`: `market_data:8/8 ready` can be reached when Hubble base URL and provider deps are present.
- A TVR OHLCV fetch should return `ok=true` and candles.

## Pitfalls

- Do not install into the wrong Python just because `python3 -m pip` exists. First prove which `python3` zsh resolves after login/profile files.
- Hermes terminal() may run non-login bash and resolve `python3` differently from the operator zsh. If bash shows `python3_provider_dependencies_missing` but zsh has deps, rerun provider checks through `zsh -lc 'cd <ict-engine-repo> && ...'` or use `<provider-python>` for fetch scripts. Treat this as shell/runtime parity, not provider failure.
- Homebrew `eval $(brew shellenv)` can re-prepend `/opt/homebrew/bin` after `.zshenv`; if so, a `.zshenv` PATH fix alone is insufficient.
- Remote TVRemix HTTP 429 is not the same as local TradingView MCP stdio failure. Use local stdio for OHLCV when available, but keep options/Greeks marked degraded unless verified.
- Hubble `provider-status ready` is config readiness, not data proof. If a direct Hubble curl returns empty/timeout, keep provider-status green but require per-request fetch validation before using Hubble rows as evidence.
- `provider-status ready` is still only liveness. Run a concrete `market-data-harness` fetch before claiming provider evidence.
