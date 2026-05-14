# Kaggle Public API Regime Source Audit

Run ID: `20260511T100252+0800-codex-kaggle-public-api-regime-source-audit`

## Scope

Used the public Kaggle dataset list API for `market regime`, then audited the only newly relevant small candidate not already covered by the `20260511T094205` stock-regime panel audit.

## Candidate

`igormerlinicomposer/herding-based-market-regime-dataset`

- Downloadable: true.
- Raw files inspected under `/tmp` only.
- Files: `alpha_trading_signals.csv`, `risk_analysis_output.csv`.
- Observed columns include `Date`, `Risk_Score`, `Risk_State`, `Position`, and `Trend`.

## Rejection

- No instrument field.
- No timeframe field.
- No active MainRegimeV2 root labels: `Bull`, `Bear`, `Sideways`, `Crisis`.
- `Risk_State`/`Trend`/`Position` are derived herding/trading signals, not an exact-underlying independent parent-root label panel.
- No timestamped direct `Manipulation` positive/negative rows.

## Result

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Gate result: `blocked_kaggle_public_api_search_no_new_accepted_source_labels`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
