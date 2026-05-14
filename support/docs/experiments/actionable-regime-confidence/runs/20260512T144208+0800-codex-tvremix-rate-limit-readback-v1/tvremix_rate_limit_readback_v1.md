# TVR Rate-Limit Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T144208+0800-codex-tvremix-rate-limit-readback-v1/`

## Scope

This is a narrow TradingViewRemix/TVR health repro after the `141554` provider matrix reported `tradingview_mcp_connectivity_probe_failed`.

The local config file exists at `~/.ict-engine/tvremix_mcp.json` with `url` and `api_key` keys present. The API key was not printed, stored, or committed.

## Probe

Command shape:

```sh
curl -m 25 -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <redacted>' \
  --data-binary '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  '<configured TVR MCP URL>'
```

Observed response:

- HTTP status: `429`
- Body: `Rate limit exceeded. Retry after 62344s.`

## Decision

TVR is not missing local config in this readback. It is live-service rate-limited for the current MCP credential/path, so it remains a provider-context gap for Board A until the retry window clears or a refreshed credential/path is supplied.

This does not run Auto-Quant, Pre-Bayes/BBN, CatBoost/path-ranker, or execution-tree admission. It is provider-health evidence only.

Net Board A effect remains fail-closed: accepted `>=95%` contexts `0`; strict full objective false; trade usable false; promotion allowed false; and `update_goal=false`.

