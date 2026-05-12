# Same-Root Six-Provider 1h AQ v1

Run id: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`
Source repair reference: `20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1`
IBKR repair reference: `20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1`
TVR precheck reference: `20260512T112030+0800-codex-btc-comparable-tvr-ibkr-provider-preflight-v1`

## Scope
This packet attempts one same-root provider/AQ authority run with YF, Kraken, Binance, Bybit, TVR default remote/configured path, and IBKR PAXOS 30D 1h MIDPOINT.
It does not edit ict-engine runtime code, rewrite older roots, approve selected history, or promote a candidate.

## Provider Fetch Matrix
- `yfinance_btc_usd_1h`: exit `0`, rows `971`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/input-csv/yfinance_btc_usd_1h.csv`.
- `kraken_xbtusd_1h`: exit `0`, rows `721`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/input-csv/kraken_xbtusd_1h.csv`.
- `binance_btcusdt_1h`: exit `0`, rows `985`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/input-csv/binance_btcusdt_1h.csv`.
- `bybit_btcusdt_linear_1h`: exit `0`, rows `985`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/input-csv/bybit_btcusdt_linear_1h.csv`.
- `tvr_default_binance_btcusdt_1h`: exit `0`, rows `720`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/input-csv/tvr_default_binance_btcusdt_1h.csv`.
- `ibkr_paxos_btc_30d_1h_midpoint`: exit `0`, rows `783`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/input-csv/BTC_1h_midpoint.csv`.

## AQ Results
- `yfinance`: rows `971`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `13`, profit_pct `1.83`, win_rate_pct `53.84615384615385`, profit_factor `1.837494864219173`.
  - `ProviderCryptoPullbackRevertV1`: trades `8`, profit_pct `-0.18`, win_rate_pct `37.5`, profit_factor `0.8671168003674068`.
- `kraken_public`: rows `721`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `23`, profit_pct `-0.55`, win_rate_pct `34.78260869565217`, profit_factor `0.8609310567518771`.
  - `ProviderCryptoPullbackRevertV1`: trades `9`, profit_pct `-0.71`, win_rate_pct `22.22222222222222`, profit_factor `0.5831340534022595`.
- `binance_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `37`, profit_pct `0.77`, win_rate_pct `37.83783783783784`, profit_factor `1.1326410355009617`.
  - `ProviderCryptoPullbackRevertV1`: trades `15`, profit_pct `-0.98`, win_rate_pct `26.666666666666668`, profit_factor `0.5850842589000907`.
- `bybit_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `-1.71`, win_rate_pct `23.52941176470588`, profit_factor `0.45016637432495576`.
- `tvr_default_binance`: rows `720`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `25`, profit_pct `-1.03`, win_rate_pct `32.0`, profit_factor `0.765930096934388`.
  - `ProviderCryptoPullbackRevertV1`: trades `12`, profit_pct `-1.47`, win_rate_pct `16.666666666666664`, profit_factor `0.34369888998507653`.
- `ibkr_paxos_long_midpoint`: rows `783`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `32`, profit_pct `0.98`, win_rate_pct `37.5`, profit_factor `1.1923059186034541`.
  - `ProviderCryptoPullbackRevertV1`: trades `12`, profit_pct `-0.27`, win_rate_pct `25.0`, profit_factor `0.8524420093984961`.

## Decision
- Gate result: `same_root_six_provider_1h_aq_v1=six_provider_1h_provider_aq_packet_ready_for_downstream_no_promotion`.
- Provider fetch success: `6/6`.
- Successful AQ provider runs: `6/6`.
- Strategies with metrics: `12`.
- Total trades in AQ metrics: `237`.
- Mature rooted branch observations added: `237`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Fail-Closed / Next
- No Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree promotion chain is claimed from this packet.
- If all six provider fetches and all six AQ lanes are successful, the next slice must push the selected surviving branch through the ordered downstream chain from this same run root.
- If any provider fetch or AQ lane is missing, this packet remains fail-closed infrastructure evidence only.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/same-root-six-provider-1h-aq-v1/same_root_six_provider_1h_aq_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/same-root-six-provider-1h-aq-v1/prompt_to_artifact_checklist_same_root_six_provider_1h_aq_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/checks/same_root_six_provider_1h_aq_v1_assertions.out`
- Command output and exits: `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/command-output`, `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/checks`
- Input CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/input-csv`
- AQ provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/workspace`
