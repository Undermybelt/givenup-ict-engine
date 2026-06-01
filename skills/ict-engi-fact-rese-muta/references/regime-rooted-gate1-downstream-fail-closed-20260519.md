# Regime-rooted Gate1 and downstream fail-closed examples - 2026-05-19

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use this as a compact reference for future ict-engine profitability-factor loops.

## Kraken BAT/ZRX 1m ladder

Root:

`crypto -> kraken_spot -> BATUSD/ZRXUSD -> 1m -> VolatilityCompression -> BrowserUtilityAltcoinVwapReclaim -> one_minute_vwap_reclaim_density_full_ladder -> kraken_bat_zrx_vwap_reclaim_density_1m_full_ladder_v1`

Result:

- Provider: `kraken_public`, `local_cache_replay=false`.
- Covered timeframes: `1m/5m/15m/30m/1h/4h/1d`.
- `rank_rows=14`, `rank_total_trade_count=75`, `rank_positive_rows=2`.
- `positive_origin_1m=[]`.
- Positive higher timeframe existed: `BATUSD 1h`.
- `cost_gate_survives=false`.
- Decision: `drop_or_block_gate1_practical`; no downstream.

Lesson: positive higher-timeframe siblings do not rescue a failed `1m` root. If a higher timeframe looks interesting, reopen it as its own exact root.

## CRWD 5m PDA/MTF soft-confirmation downstream

Root:

`US_EQ -> single_stock -> CRWD -> 5m -> RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1`

Gate 1 result:

- `CRWD 5m`: 43 trades, win rate `62.7907%`, total profit `5.81%`, Sharpe `6.0837`.
- Cost stress survived: 2 bps side `+4.09%`, 5 bps side `+1.51%`.

Downstream readback after exact branch run and post-ranker retry:

- Exact branch survived.
- `transition_hazard=0.5950369253623637`, barely under `0.60`.
- `pda_hybrid_alignment=true`.
- `execution_readiness=0.3741236047533753`, far below `0.65`.
- `execution_tree_gate_status=blocked`, `execution_tree_branch=block_crowded`.
- Ranker not validation-ready; fallback/runtime visibility is not promotion.
- Decision: `exact_crwd_5m_downstream_fail_closed`; observation/scoped candidate only.

Useful retry sequence when downstream initially lacks ranker visibility:

1. Run `path_ranker_integration.py --python-runner system --allow-direct-fallback --register-runtime-artifact` if `uv`/CatBoost bootstrap is fragile or the current target has too few rows.
2. Run `apply-structural-path-ranking-external-scores`.
3. Run `enable-structural-path-ranking-runtime --reuse-mode candidate_set_only`.
4. Rerun `analyze` and `workflow-status --refresh`.
5. Re-read `execution_tree_trace.json`, workflow, and terminal summary.
6. If validation rows are still immature or execution readiness remains below `0.65`, keep fail-closed; do not describe fallback visibility as live readiness.

## Medical diagnostics 1m dense RSI/VWAP reclaim

Root:

`RangeReversion -> MedicalDiagnosticsOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_medical_diagnostics_rsi_vwap_reclaim_1m_dense_v1`

Result:

- Provider: `yfinance/YF`, `local_cache_replay=false`.
- Symbols: `DGX/LH/IDXX`.
- Attempted timeframes: `1m/5m/15m/30m/1h/4h/1d`.
- Some higher timeframe provider windows failed; preserve as provider-window gaps, not factor proof.
- `rank_rows=13`, `total_trades=570`, `origin_trades_1m=50`.
- `1m` rows were negative:
  - `LH/1m`: 17 trades, `-0.11%`.
  - `DGX/1m`: 14 trades, `-0.68%`.
  - `IDXX/1m`: 19 trades, `-1.40%`.
- Higher timeframe positive: `DGX/30m`, 41 trades, `+4.66%`.
- Decision: drop current `1m` root; no downstream.

Lesson: even high trade count is not enough if the exact `1m` origin is negative. A positive `30m` sibling must become a new exact root and may use `1m` only as context, not as proof.

## Practical decision rule

For every candidate, write terminal evidence in this order:

1. Full branch root including market/product/symbol/timeframe/regime/profit factor.
2. Provider provenance and `local_cache_replay` flag.
3. Per-timeframe Gate1 verdict, especially exact origin timeframe.
4. 0/1/2/5 bps cost stress.
5. Downstream allowance only if exact root survives density and cost.
6. Downstream readback: exact path, Pre-Bayes/BBN/CatBoost/ranker/execution tree, `transition_hazard`, `pda_hybrid_alignment`, `execution_readiness`.
7. Final state: `keep`, `drop`, `incubate/observation`, or `handoff`, never live-ready unless all gates pass.
