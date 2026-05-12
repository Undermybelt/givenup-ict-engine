# Six-Provider BTC Local-TV Stdio AQ Same-Root Repair v2

Run id: `20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1`
Repair id: `same-root-repair-v2`

## Scope
Run-local repair of the attempt-1 same-root AQ workspace defect.
Inputs are the existing `162400/provider-csv/` files only; no provider refetch and no downstream chain.

## Provider Inputs
- `yfinance`: rows `983`.
- `kraken_public`: rows `721`.
- `binance_public`: rows `985`.
- `bybit_public`: rows `985`.
- `tvr_local_stdio`: rows `720`.
- `ibkr_aggtrades`: rows `787`.

## AQ Results
- `yfinance`: rows `983`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/workspace/same-root-repair-v2/auto-quant-112315-yfinance`.
  - `ProviderCryptoMomentumStateV1`: trades `14`, profit_pct `1.69`, win_rate_pct `50.0`, profit_factor `1.7314733582840918`.
  - `ProviderCryptoPullbackRevertV1`: trades `8`, profit_pct `-0.21`, win_rate_pct `37.5`, profit_factor `0.8505535234732061`.
- `kraken_public`: rows `721`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/workspace/same-root-repair-v2/auto-quant-112315-kraken_public`.
  - `ProviderCryptoMomentumStateV1`: trades `23`, profit_pct `-0.55`, win_rate_pct `34.78260869565217`, profit_factor `0.8609310567518771`.
  - `ProviderCryptoPullbackRevertV1`: trades `9`, profit_pct `-0.71`, win_rate_pct `22.22222222222222`, profit_factor `0.5831340534022595`.
- `binance_public`: rows `985`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/workspace/same-root-repair-v2/auto-quant-112315-binance_public`.
  - `ProviderCryptoMomentumStateV1`: trades `37`, profit_pct `0.77`, win_rate_pct `37.83783783783784`, profit_factor `1.1326410355009617`.
  - `ProviderCryptoPullbackRevertV1`: trades `15`, profit_pct `-0.98`, win_rate_pct `26.666666666666668`, profit_factor `0.5850842589000907`.
- `bybit_public`: rows `985`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/workspace/same-root-repair-v2/auto-quant-112315-bybit_public`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `-1.71`, win_rate_pct `23.52941176470588`, profit_factor `0.45016637432495576`.
- `tvr_local_stdio`: rows `720`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/workspace/same-root-repair-v2/auto-quant-112315-tvr_local_stdio`.
  - `ProviderCryptoMomentumStateV1`: trades `10`, profit_pct `-0.65`, win_rate_pct `40.0`, profit_factor `0.6867694918857996`.
  - `ProviderCryptoPullbackRevertV1`: trades `6`, profit_pct `-0.83`, win_rate_pct `16.666666666666664`, profit_factor `0.40539240394914555`.
- `ibkr_aggtrades`: rows `787`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/workspace/same-root-repair-v2/auto-quant-112315-ibkr_aggtrades`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `0.08`, win_rate_pct `38.23529411764706`, profit_factor `1.0144516414659697`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `1.31`, win_rate_pct `52.94117647058824`, profit_factor `1.6850347091222428`.

## Same-Root Checks
- Workspace file count: `84`.
- Derived metric count: `12`.
- All workspaces under repair root: `True`.
- Old-root output references: `0`.

## Decision
- Gate result: `same_root_repair_v2=same_root_six_provider_aq_present_downstream_not_started_no_promotion`.
- Successful AQ provider runs: `6/6`.
- Strategies with metrics: `12`.
- Total trades in AQ metrics: `224`.
- Same-root six-provider AQ authority: `True`.
- IBKR first-class AQ success: `True`.
- Downstream chain is not started in this repair step.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/six-provider-btc-local-tvr-aq-same-root-repair-v2/same_root_repair_v2.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/six-provider-btc-local-tvr-aq-same-root-repair-v2/prompt_to_artifact_checklist_same_root_repair_v2.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/checks/same-root-repair-v2/same_root_repair_v2_assertions.out`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/command-output/same-root-repair-v2`
- Checks: `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/checks/same-root-repair-v2`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/workspace/same-root-repair-v2`
