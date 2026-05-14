# Cross-Market Timeframe Validation Packet Preflight v1

- Source packet: `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/feasible-window-same-root-aq-packet-v1/feasible_window_same_root_aq_packet_v1.json`
- Provider rows inventoried: `6`
- Real AQ feedback rows: `1953`
- Cleaned downstream data files: `1`
- Promotion allowed: `false`
- Trade usable: `false`
- Gate decision: `fail_closed`

## Gate Matrix

| Gate | Status | Evidence |
|---|---|---|
| `six_provider_aq_surface` | `pass` | provider/AQ surface present |
| `aq_trade_rows_present` | `pass` | real_trade_rows=1953 |
| `independent_cross_market_downstream` | `fail_closed` | provider_markets=6 but downstream validation rows=0 |
| `independent_cross_timeframe_downstream` | `fail_closed` | cleaned_timeframes=1h |
| `raw_scored_mature_min30` | `fail_closed` | history_mature_rows=0 history_raw_score_rows=4 |
| `production_validation_min30` | `fail_closed` | mature_rows=0 |
| `observation_validation_min30` | `pass` | observation trade rows from AQ feedback=1953; still not production validation |
| `per_regime_calibrated_95` | `fail_closed` | no artifact proves every visible regime calibrated >=0.95 |
| `catboost_path_ranker_ready` | `fail_closed` | calibrated_rows=0 |
| `execution_tree_non_observe` | `fail_closed` | latest execution candidate remains non-promoting/no-trade in source packet |

## Readback

The six-provider AQ surface and real AQ trade feedback are present, but this preflight does not find independent downstream cross-market/timeframe validation rows, mature production-validation rows, or per-regime calibrated `>=95%` acceptance evidence.

Existing related packets are recorded as inventory only and are not counted as support for this claim because they are not a fresh full Board A downstream validation packet under the current acceptance contract.

## Next

Open a new isolated full-chain validation run only after independent cross-market/timeframe inputs can produce >=30 mature production-validation rows and per-regime calibrated >=95% evidence.

Do not promote Board A from this preflight.
