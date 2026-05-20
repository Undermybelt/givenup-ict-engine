# 2026-05-20 pandas-datareader hotplug handoff TODO

Owner: Hermes GPT-5.5 CLI
Started: 2026-05-20 20:08 CST
Status: active

## Goal

Add a zero-config, consumer-safe, token-friendly, no-pollution pandas-datareader hotplug path for optional external market/macro/reference data. Keep existing native yfinance as default. Let users explicitly opt into richer pandas-datareader sources.

## Non-goals

- Do not replace native yfinance default.
- Do not make pandas-datareader a required dependency.
- Do not mark any pandas-datareader output as trade-ready.
- Do not vendor external repos or write generated data into the repo.
- Do not consume docs as runtime inputs.

## User-specific desired data content

Initial opt-in sources to support:

1. FRED macro regime covariates: rates, volatility, credit/liquidity stress series.
2. Fama-French style factors: equity residual-alpha / style-exposure diagnostics.
3. Stooq/Yahoo daily reference OHLCV: no-key historical backfill and fallback inspection.
4. Yahoo actions/dividends/splits: corporate-action adjustment checks.

## Design constraints

- Zero-config: CLI surfaces and tests work without pandas-datareader installed.
- Hot-plug: actual network fetch requires explicit source selection and optional package install.
- Token-friendly: compact JSON by default, bounded rows, clear provenance/error category.
- No pollution: generated fetch output goes to stdout or explicit output path, never repo root by default.
- No debt: typed error categories and capability metadata; no hidden personal defaults.

## TODO

- [x] Route and read repo contracts.
- [x] Create this handoff TODO.
- [x] Add zero-config pandas-datareader bridge script with capability and demo modes.
- [x] Add tests for capability/demo/error surfaces.
- [x] Wire optional provider metadata into provider-status / harness where minimal and safe.
- [x] Add docs/readme note if needed.
- [x] Run focused tests and provider-status smoke.
- [x] Update skill reference if reusable lesson changes.
- [x] Commit coherent slice only, preserving unrelated dirty work.

## Running log

- 2026-05-20 20:08 CST: Created handoff. Current worktree is already dirty with many unrelated tracked/untracked files; commit must stage explicit paths only.
- 2026-05-20 20:12 CST: Added `support/scripts/research/pandas_datareader_hotplug.py` and zero-config unit tests. Bridge defaults to capability/demo surfaces, keeps `trade_usable=false`, and requires explicit `--source` for real provider fetch.
- 2026-05-20 20:17 CST: Added `pandas_datareader` to `provider-status` market-data catalog as explicit opt-in optional dependency. It is selectable by user, never default-enabled, and reports module presence without failing zero-config.
- 2026-05-20 20:22 CST: All tasks complete. Verification: Python 4/4 tests pass; Rust provider_catalog test passes; `provider-status --compact` shows `pandas_datareader` in market_data ready set; `pandas_datareader_hotplug.py --capabilities` returns ok/zero_config/4 sources/5 defaults; `--demo` returns ok/fixture_only/3 rows/net=False; `market-data-harness plan` unaffected. Handoff Done.
