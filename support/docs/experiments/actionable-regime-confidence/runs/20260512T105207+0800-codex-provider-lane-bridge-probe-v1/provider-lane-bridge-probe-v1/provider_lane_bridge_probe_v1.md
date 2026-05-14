# Provider Lane Bridge Probe v1

Run id: `20260512T105207+0800-codex-provider-lane-bridge-probe-v1`
Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1`

## Purpose
Low-pollution provider-lane bridge probe after the hard provider matrix failed closed. This artifact records concrete fetch attempts without changing ict-engine runtime code or promoting Board A.

## Results
- OK providers: `binance_public_ccxt, bybit_public_ccxt, ibkr_ad_hoc_uv, kraken_public_ccxt, yfinance`
- Failed/partial providers: `tradingview_mcp_harness`
- Six-provider promotion matrix passed: `false`
- Accepted rows added: `0`
- Promotion allowed: `false`
- update_goal: `false`

## Evidence
- Public probe summary: `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/provider-lane-bridge-probe-v1/public_provider_ohlcv_probe_v1.json`
- Consolidated JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/provider-lane-bridge-probe-v1/provider_lane_bridge_probe_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/provider-lane-bridge-probe-v1/prompt_to_artifact_checklist_provider_lane_bridge_probe_v1.csv`
- IBKR CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/provider-csv/ibkr_QQQ_1h_5d.csv` rows=80
- TVR stdout/stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/command-output/02_tradingview_mcp_qqq_1d_fetch.out`, `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/command-output/02_tradingview_mcp_qqq_1d_fetch.err`

## Decision
This advances provider-lane evidence only. It may show that public no-login crypto data can be fetched with an isolated uv runtime even while the default `provider-status` catalog remains fail-closed under system Python. It does not satisfy Board A promotion because strict catalog readiness, TradingViewRemix, selected-history/source-control, and downstream regime-chain gates remain unresolved.
