# HF Root Label Candidate Materialization

Run id: `20260511T073900+0800-codex-hf-root-label-candidate-materialization`

Goal achieved: `false`

## Materialized Candidates

| Dataset | Local Raw Status | Labels | Fit To MainRegimeV2 Full Matrix |
|---|---|---|---|
| `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD` | downloaded train CSV to `/private/tmp`; not committed | `Choppy High-Vol`, `Range`, `Squeeze`, `Strong Trend`, `Volatility Spike`, `Weak Trend` | BTC-only 5m/15m HMM-derived labels; sidecar candidate only |
| `AAdevloper/nifty50-market-regime` | downloaded CSV to `/private/tmp`; not committed | `RISK_OFF`, `RISK_ON` | NIFTY-only binary regime; sidecar candidate only |
| `sujinwo/tsie-market-regime-dataset` | README/schema inspected only | 7 rule-based buy/sell/noise/trap classes | IDX-only rule-derived labels; mapping audit needed, not full root panel |

## Counts

- BTC HMM6 train rows: `220,717`
- BTC HMM6 label counts: `Range=47,151`, `Weak Trend=43,380`, `Strong Trend=40,758`, `Squeeze=39,677`, `Choppy High-Vol=32,204`, `Volatility Spike=17,547`
- NIFTY rows: `2,235`
- NIFTY labels: `RISK_OFF=1,216`, `RISK_ON=1,019`

## Accounting

These sources prove that public regime-label candidates exist, but they still do not complete the expanded Board A objective:

- no candidate supplies all four `Bull` / `Bear` / `Sideways` / `Crisis` roots;
- no candidate attaches labels to every ready yfinance/Kraken symbol/timeframe cell;
- HMM/rule-derived labels are useful sidecar/provenance, not automatically independent accepted root labels.

Gate result: `blocked_hf_candidates_materialized_but_not_full_mainregimev2_panel`.

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

