# YF 1m-root ladder blocked with positive siblings

Use when a 1m-root profit-factor branch is requested but fresh provider coverage is partial.

Session pattern
- Branch tested: `US -> equity_sector_etf -> XLU -> 1m -> Range -> DefensiveLiquidity -> vwap_reclaim_density -> yf_xlu_defensive_utilities_vwap_reclaim_autoresearch_1m_mtf_v1`.
- Fresh YF fetch produced real rows for `5m/15m/30m/1h/1d`.
- Root `1m` failed provider fetch with Yahoo SSL EOF; `4h` was not accepted by the local Yahoo fetch contract.
- Vectorized proxy showed some positive sibling/context rows (`15m`, `30m`) but did not satisfy 1-3 trades/day and did not preserve an exact `1m` root pass.

Durable lesson
- Do not run Pre-Bayes/BBN/CatBoost/execution-tree when the explicit root timeframe has no fresh provider rows or no exact Auto-Quant Gate 1 pass.
- Positive sibling/context frames are candidate-discovery evidence only. They can seed a new independent sibling-root experiment, but cannot rescue or promote the failed `1m` root.
- If using a vectorized proxy for triage, label it as proxy/candidate-discovery and rerun exact Auto-Quant materials before any promotion claim.
- For `4h` under Yahoo, verify the fetch contract first. If unsupported, either omit it with an explicit missing-timeframe note or build a clearly labeled resampled/context artifact; never silently treat `1h` as native `4h`.

Minimum packet fields
- `branch_path`
- `root_timeframe`
- `provider_rows[]` with `timeframe`, `rows`, `first`, `last`, `provider`, `local_cache_replay`
- `missing_timeframes[]`
- `cost_model`
- `downstream_allowed=false` when root Gate 1 is blocked
- reason naming the exact missing root property
