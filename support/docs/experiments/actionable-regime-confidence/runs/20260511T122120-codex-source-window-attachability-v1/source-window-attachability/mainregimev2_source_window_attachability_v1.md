# MainRegimeV2 Source-Window Attachability v1

Run ID: `20260511T122120+0800-codex-source-window-attachability-v1`

## Purpose

This run converts the positive source-window pivot into an attachability check. It separates three things that were getting conflated:

- source-label target slots;
- calibrated abstaining factor gates;
- full-market/full-timeframe completion.

## Source-Label Slots

Accepted native source-label target slots added: `2`.

| Root | Provider | Instrument | Timeframe | Rows | Status |
|---|---|---|---|---:|---|
| `Bull` | `yfinance` | `^GSPC` | `1d` | `4464` | `native_exact_sp500_daily_closed_windows` |
| `Bear` | `yfinance` | `^GSPC` | `1d` | `1211` | `native_exact_sp500_daily_closed_windows` |
| `Crisis` | `n/a` | `US macro/business cycle` | `month` | `0` | `requires_owner_crosswalk_before_instrument_attachment` |
| `Sideways` | `n/a` | `n/a` | `n/a` | `0` | `missing_dated_source_or_owner_approved_adjudication_protocol` |

## Native `^GSPC` Daily Gate

| Root | Rule | Calibration Wilson95 | Test Wilson95 | Calibration Support | Test Support | Accepted |
|---|---|---:|---:|---:|---:|---:|
| `Bull` | `vol20 <= 0.109670170889` | `0.994911` | `0.962280` | `751` | `98` | `True` |
| `Bear` | `ma_gap20 <= -0.066403763953 AND ret40 <= -0.101798358916` | `0.524108` | `0.565518` | `14` | `5` | `False` |

## Decision

- Source-label target slots added: `2` for native `^GSPC` daily `Bull`/`Bear` closed Yardeni windows.
- Calibrated source-window gates accepted: `Bull`.
- Full objective achieved: `false`.
- Gate result: `accepted_native_bull_source_window_gate_and_two_sp500_source_label_slots_full_matrix_still_open`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw yfinance cache committed: false.

## Next

Use the accepted `Bull` source-window gate as a positive bridge from source labels to a calibrated factor. Do not retry generic source scans. The next productive closure is either:

1. get an explicit owner-approved crosswalk for S&P 500 source windows to SPY/ES/timeframe projections, then rerun this same attachability check; or
2. define a dated `Sideways` adjudication protocol, because residual-from-Bull/Bear is still not a source label.
