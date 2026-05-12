# MainRegimeV2 Local Panel Rule Probe

Run ID: `20260511T104942+0800-codex-mainregimev2-local-panel-rule-probe`

Source root: `/Users/thrill3r/Downloads/stock-market-regimes-20002026`

## Readback

- The source labels are parent-class `MainRegimeV2` labels: `Bull`, `Bear`, `Sideways`, and `Crisis`.
- Extra labels mapped to residual/provenance only: `['High-volatility']`.
- Rows: `245021` total; `245005` MainRegimeV2 rows.
- Native timeframe: `1d` only.
- `Manipulation` is not present and is not inferable from this OHLCV/macro panel.

## Selective Rule Probe

| Root | Accepted 95 | Rule | Cal support | Cal Wilson95 | Test support | Test Wilson95 |
|---|---:|---|---:|---:|---:|---:|
| Bull | true | `drawdown_252 >= -0.002313918074873498` | 5332 | 0.986810 | 4581 | 0.990923 |
| Bear | false | `range_pos_252 <= 0` | 619 | 0.845519 | 807 | 0.951759 |
| Sideways | false | `abs_ma_ratio_252 <= 0.005983289330013457 AND abs_ret_20 <= 0.01746949514288885` | 373 | 0.707169 | 296 | 0.751441 |
| Crisis | false | `vol_real_120 >= 0.06997391797413682` | 57 | 0.746753 | 0 | 0.000000 |

## Decision

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Gate result: `blocked_local_panel_selective_rule_probe_daily_only_and_incomplete_roots`.
- This confirms the user's taxonomy correction: the local panel is a main-class regime panel, while expansion/consolidation/stress/liquidity labels are child/provenance evidence only.
- The probe does not complete the Board A goal because it is daily-only, accepts only `Bull` under the local selective rule, and provides no direct `Manipulation` evidence.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
