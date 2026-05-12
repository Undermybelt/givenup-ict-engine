# Provider-Linked AQ Provenance Probe v1

Run id: `20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1`
Source provider bridge: `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1`

## Scope
This packet links provider invocation evidence to isolated Auto-Quant/TOMAC execution without changing ict-engine runtime code.
It normalizes only the public BTC provider CSVs from the provider bridge into run-local FreqTrade feathers, then runs the two existing provider-owned BTC AQ strategies per provider.
IBKR and TradingViewRemix/TVR are kept as provenance gates from the same provider bridge, not silently substituted into the BTC AQ dataset.

## Provider Provenance
- `binance_public_ccxt`: status `ok`, symbol `BTC/USDT`, rows `120`, path `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/provider-csv/binance_public_ccxt_btc_1h_120.csv`
- `bybit_public_ccxt`: status `ok`, symbol `BTC/USDT`, rows `120`, path `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/provider-csv/bybit_public_ccxt_btc_1h_120.csv`
- `ibkr_ad_hoc_uv`: status `ok`, symbol `QQQ`, rows `80`, path `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/provider-csv/ibkr_QQQ_1h_5d.csv`
- `kraken_public_ccxt`: status `ok`, symbol `BTC/USD`, rows `120`, path `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/provider-csv/kraken_public_ccxt_btc_1h_120.csv`
- `tradingview_mcp_harness`: status `failed`, symbol `NASDAQ:QQQ`, rows `None`, path `Error: market-data-harness fetch encountered failures: role=etf_reference provider=tradingview_mcp symbol=NASDAQ:QQQ fetch_failed:tradingview MCP call 'get_ohlcv' returned error | install_prompt=Consumer agent follow-up: retry a lightweight MCP health check such as tools/list before treating TradingViewRemix as usable. | install_prompt=Consumer agent request: TradingViewRemix MCP credentials were present but the live probe failed. Ask the user to re-enter ICT_ENGINE_TVREMIX_MCP_API_KEY and verify the MCP endpoint at https://tvremix.xyz/api/mcp/v1.`
- `yfinance`: status `ok`, symbol `BTC-USD`, rows `146`, path `docs/experiments/actionable-regime-confidence/runs/20260512T105207+0800-codex-provider-lane-bridge-probe-v1/provider-csv/yfinance_btc_usd_1h_7d.csv`

## Auto-Quant Results
- `yfinance`: rows `146`, compile exit `0`, TOMAC exit `0`.
  - ProviderCryptoMomentumStateV1: trades=1 profit_pct=-0.61 sharpe=-100.0 pf=0.0
  - ProviderCryptoPullbackRevertV1: trades=0 profit_pct=0.0 sharpe=0.0 pf=0.0
- `kraken_public_ccxt`: rows `120`, compile exit `0`, TOMAC exit `0`.
  - ProviderCryptoMomentumStateV1: trades=2 profit_pct=-0.52 sharpe=-30.23404338579132 pf=0.11653182396569162
  - ProviderCryptoPullbackRevertV1: trades=0 profit_pct=0.0 sharpe=0.0 pf=0.0
- `binance_public_ccxt`: rows `120`, compile exit `0`, TOMAC exit `0`.
  - ProviderCryptoMomentumStateV1: trades=2 profit_pct=-0.44 sharpe=-22.27901341939791 pf=0.2633692659067377
  - ProviderCryptoPullbackRevertV1: trades=0 profit_pct=0.0 sharpe=0.0 pf=0.0
- `bybit_public_ccxt`: rows `120`, compile exit `0`, TOMAC exit `0`.
  - ProviderCryptoMomentumStateV1: trades=2 profit_pct=-0.44 sharpe=-22.63947833040509 pf=0.2558852133885258
  - ProviderCryptoPullbackRevertV1: trades=0 profit_pct=0.0 sharpe=0.0 pf=0.0

## Decision
- Gate result: `provider_linked_aq_provenance_probe_v1=aq_ran_with_public_provider_rows_but_six_provider_gate_fail_closed_no_promotion`.
- AQ execution is real for the public provider rows above, but the packet remains fail-closed.
- TradingViewRemix/TVR is still failed, IBKR is ad hoc QQQ only and not the BTC AQ feed, and all AQ runs are short-window diagnostics.
- Accepted rows added: `0`.
- Mature rooted branch observations added: `0`.
- Promotion allowed: `false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1/provider-linked-aq-provenance-probe-v1/provider_linked_aq_provenance_probe_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1/provider-linked-aq-provenance-probe-v1/prompt_to_artifact_checklist_provider_linked_aq_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1/checks/provider_linked_aq_provenance_probe_v1_assertions.out`
- Provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1/workspace`
