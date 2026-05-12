# Six Provider AQ First-Class IBKR Repair v1

Run id: `20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1`

## Scope
This repair retries only the missing same-root yfinance and TVR lanes from the first-class IBKR packet, then runs AQ for repaired lanes with the same TOMAC template.
It does not edit ict-engine runtime code and does not run downstream promotion.

## Repair Fetches
- `22_yfinance_btc_usd_1h_venv_retry`: rows `983`, exit `0`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/provider-csv/yfinance_btc_usd_1h_retry.csv`.
- `23_tvr_btc_usd_1h_local_stdio_retry`: rows `708`, exit `0`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/provider-csv/tvr_btc_usd_1h_retry.csv`.

## Repair AQ Results
- `yfinance`: rows `983`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `14`, profit_pct `1.69`, win_rate_pct `50.0`, profit_factor `1.7314733582840918`.
  - `ProviderCryptoPullbackRevertV1`: trades `8`, profit_pct `-0.21`, win_rate_pct `37.5`, profit_factor `0.8505535234732061`.
- `tvr_btc_usd`: rows `708`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `9`, profit_pct `-0.52`, win_rate_pct `44.44444444444444`, profit_factor `0.7366872404746276`.
  - `ProviderCryptoPullbackRevertV1`: trades `6`, profit_pct `-0.8`, win_rate_pct `16.666666666666664`, profit_factor `0.4132868377965511`.

## Combined Decision
- Gate result: `115431_six_provider_aq_first_class_ibkr_repair_v1=six_provider_aq_compile0_tomac0_downstream_not_run_no_promotion`.
- Same-root six-provider AQ authority: `True`.
- Combined successful AQ provider runs: `6/6`.
- Combined strategies with metrics: `12`.
- Combined total trades: `185`.
- Mature rooted branch observations added: `185`.
- Downstream Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree promotion chain: `not_run`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
