# Optional External History Hotplug Handoff TODO

Date: 2026-05-15

Purpose: add one additive external-history lane that can feed `ict-engine` /
Auto-Quant as an opt-in source without replacing zero-config defaults or
turning any maintainer-local data shape into a public requirement.

## Task Intent Draft

Requested outcome:
- Keep zero-config consumer behavior unchanged.
- Treat external history as an optional sidecar lane, not a mandatory provider.
- Let users inspect and choose an external-history lane before adopting it.
- Keep the slice token-friendly, generic, and safe for release surfaces.
- Preserve repo hygiene: no nested workspaces, no generated data roots, no
  private paths in public output.

Non-goals:
- Do not make the gist or any CCXT fetcher a default provider.
- Do not hard-wire a private dataset root into the CLI.
- Do not add new mandatory Python dependencies to the zero-config path.
- Do not take over active Board A/B current-state docs or the current dirty
  `main.rs` lane.

## Baseline Read Set Hint

- `AGENT.md`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
- `config/market_data_harness_presets.json`
- `config/market_relationships.json`
- `support/examples/provider_profiles/`
- `support/scripts/research/market_data_resolver.py`
- `tests/provider_neutral_cli.rs`

## Impact Statement Draft

The public contract remains the same: users still get zero-config defaults
first. This slice only adds an inspectable opt-in external-history lane plus a
small normalization helper, so a user can keep using the generic defaults or
explicitly reuse a local normalized history pack for factor research / managed
Auto-Quant handoff.

## Todo Checkpoint Draft

Status legend: `done`, `active`, `next`, `blocked`, `not_yet`.

| Status | Item | Evidence / Notes |
|---|---|---|
| done | Scope the slice to additive hotplug surfaces only | Avoid active dirty-tree owners: `main.rs`, Board A/B current docs, and existing `fetch_external.py` edits. |
| done | Create a new handoff TODO authority for this slice | This file is the authority for the optional external-history hotplug implementation. |
| done | Add a repo example opt-in external-history profile | Added `support/examples/provider_profiles/thrill3r-nq-external-history-v1.json`; zero-config still prefers yfinance. |
| done | Add resolver support for external-history inspection hints | `support/scripts/research/market_data_resolver.py` now preserves `source_kind`, format hints, adoption mode, runtime-input mode, and conversion/path hints from opt-in profiles. |
| done | Add a standalone history normalizer helper | Added `support/scripts/auto_quant_external/normalize_external_ohlcv.py` for CSV/JSON/parquet -> `ict-engine` candle JSON normalization. |
| done | Focused verification for the new lane | `py_compile`, two Python unittest modules, and `cargo test --test provider_neutral_cli -- --nocapture` all passed. |
| done | Optional commit decision | This slice is isolated enough to commit independently; only the new hotplug profile/resolver/normalizer/tests/doc files should be staged, and the wider dirty tree must remain untouched. |
| done | Real external-source profile/readback smoke | `workflow-status --symbol NQ --state-dir /tmp/ict-engine-external-history-smoke/state-profile --profile thrill3r-nq-external-history-v1 --agent` surfaced `selected_profile_id=thrill3r_nq_external_history_v1`, the new profile contracts, and the `external_history_reuse:pending:external_http_runtime` opt-in track while keeping zero-config yfinance ready. |
| done | Real external-source normalization smoke | Public Binance klines JSON normalized successfully to `/tmp/ict-engine-external-history-smoke/btcusdt.binance.1h.normalized.json` with `300` rows via `normalize_external_ohlcv.py`. |
| done | Engine consumer smoke on normalized external JSON | `cargo run --quiet -- analyze --symbol BTCUSDT_EXT_1H --data-htf ... --data-mtf ... --data-ltf ... --state-dir /tmp/ict-engine-external-history-smoke/state-analyze --human` exited `0`; runtime readback reported `market_state=RangeConsolidation/WideRange`, `execution=observe/transition_guardrail/guarded`, `quality=0.556`. |
| done | Auto-Quant handoff + prepare smoke on normalized external JSON | `factor-research --backend auto-quant --auto-quant-profile synthetic_ohlcv` created a real handoff for `BTCUSDT_EXT_1H`; `auto-quant-status` moved from `dependency_ready_data_missing` to `dependency_ready_data_ready` after `auto-quant-prepare`, and generated `BTCUSDT_EXT_1H_USD-{1h,4h,1d}.feather` under the managed workspace. |
| done | Auto-Quant runtime pair alias repair | `synthetic_ohlcv` now normalizes runtime-only workflow symbols like `BTCUSDT_EXT_1H` down to AQ pair aliases like `BTCUSDT/USD`; the v2 smoke moved past `OperationalException: No pair in whitelist.` |
| done | Auto-Quant feather datetime repair | `prepare_external.py` now preserves datetimelike `date` columns in Feather output; the v3 smoke moved past `Can only use .dt accessor with datetimelike values.` |
| done | Auto-Quant source-derived timerange repair | `synthetic_ohlcv` now writes `config.tomac.json` timerange from the actual source candle range instead of a stale template window; the v4 smoke moved past `No data found. Terminating.` |
| done | Auto-Quant runtime execution beyond prepare | `uv run --with ta-lib --with freqtrade /tmp/ict-engine-external-history-smoke-v4/state-factor/.deps/auto-quant/run_tomac.py` exited `0` with `Done: 1 succeeded, 0 failed.` Current result is a valid AQ runtime smoke with `trade_count=0`, which is acceptable as an intake/runtime proof even though it is not yet a profitable candidate. |
| done | Auto-Quant adoption review after runtime repair | `auto-quant-adoption-review --symbol BTCUSDT_EXT_1H --state-dir /tmp/ict-engine-external-history-smoke-v4/state-factor` returned `review_status=ready_for_external_execution`, `data_ready=true`, `dependency_healthy=true`. |
| done | Add explicit consumer adoption helper | Added `support/scripts/research/external_history_adoption.py`; it emits a token-friendly adoption bundle plus `suggested_commands.sh` so a user can inspect and choose the opt-in lane without touching mainline defaults. |
| done | Longer-window non-zero AQ runtime smoke | `1000 x 1h` Binance BTCUSDT input in `/tmp/ict-engine-external-history-smoke-v5` ran through the same lane and produced `trade_count=5`, `total_profit_pct=1.12`, `sharpe=0.6437`, `win_rate_pct=80.0`, `profit_factor=1.5635`. |

## Working Direction

Recommended shape:
1. Add a new opt-in provider profile for normalized external history.
2. Extend the market-data resolver bundle so the profile can surface
   source-kind / format / adoption hints without being selected by default.
3. Add a standalone normalization helper for external OHLCV inputs.
4. Prove the new lane appears as a choice while `selected_profile_id` remains
   empty on zero-config workflow surfaces.

## Current Slice Evidence

- New opt-in profile:
  `support/examples/provider_profiles/thrill3r-nq-external-history-v1.json`
- Resolver support:
  `support/scripts/research/market_data_resolver.py`
- Normalizer helper:
  `support/scripts/auto_quant_external/normalize_external_ohlcv.py`
- Focused tests:
  - `support/scripts/auto_quant_external/tests/test_normalize_external_ohlcv.py`
  - `support/scripts/research/tests/test_market_data_resolver.py`
  - `tests/provider_neutral_cli.rs`

Verification commands run:
- `python3 -m py_compile support/scripts/auto_quant_external/normalize_external_ohlcv.py support/scripts/research/market_data_resolver.py support/scripts/auto_quant_external/tests/test_normalize_external_ohlcv.py support/scripts/research/tests/test_market_data_resolver.py`
- `python3 -m unittest support/scripts/auto_quant_external/tests/test_normalize_external_ohlcv.py -v`
- `python3 -m unittest support/scripts/research/tests/test_market_data_resolver.py -v`
- `cargo test --test provider_neutral_cli -- --nocapture`

Observed result:
- Python normalizer tests: `3 passed`
- Market-data resolver tests: `4 passed`
- `provider_neutral_cli`: `21 passed`

## 2026-05-15 Real Smoke Packet

Run root:
- `/tmp/ict-engine-external-history-smoke`

External-source notes:
- Public Stooq CSV was rejected as a friction-heavy candidate for this slice because it now requires an interactive API key/captcha flow. The failure was external-source policy friction, not a repo/runtime parsing bug.
- Public Binance klines JSON was accepted as the real smoke source because it is read-only, unauthenticated, and matches the gist-style OHLCV shape closely.

Commands run:
- `cargo run --quiet -- workflow-status --symbol NQ --state-dir /tmp/ict-engine-external-history-smoke/state-profile --profile thrill3r-nq-external-history-v1 --agent`
- `python3 support/scripts/research/market_data_resolver.py --repo-root . --market NQ --profile thrill3r_nq_external_history_v1 --output-dir /tmp/ict-engine-external-history-smoke/resolver --timeframe 1d --bar-count 120`
- `curl -L --max-time 20 'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=300' -o /tmp/ict-engine-external-history-smoke/btcusdt.binance.1h.json`
- `python3 support/scripts/auto_quant_external/normalize_external_ohlcv.py --input /tmp/ict-engine-external-history-smoke/btcusdt.binance.1h.json --output /tmp/ict-engine-external-history-smoke/btcusdt.binance.1h.normalized.json --symbol BTCUSDT`
- `cargo run --quiet -- analyze --symbol BTCUSDT_EXT_1H --data-htf /tmp/ict-engine-external-history-smoke/btcusdt.binance.1h.normalized.json --data-mtf /tmp/ict-engine-external-history-smoke/btcusdt.binance.1h.normalized.json --data-ltf /tmp/ict-engine-external-history-smoke/btcusdt.binance.1h.normalized.json --state-dir /tmp/ict-engine-external-history-smoke/state-analyze --human`
- `cargo run --quiet -- factor-research --symbol BTCUSDT_EXT_1H --data /tmp/ict-engine-external-history-smoke/btcusdt.binance.1h.normalized.json --objective regime_conditioned_profitability --backend auto-quant --auto-quant-profile synthetic_ohlcv --state-dir /tmp/ict-engine-external-history-smoke/state-factor --human`
- `cargo run --quiet -- auto-quant-status --state-dir /tmp/ict-engine-external-history-smoke/state-factor --output-format json`
- `cargo run --quiet -- auto-quant-prepare --state-dir /tmp/ict-engine-external-history-smoke/state-factor`
- `uv run --with ta-lib --with freqtrade /tmp/ict-engine-external-history-smoke/state-factor/.deps/auto-quant/run_tomac.py`

Outcome summary:
- The opt-in external-history profile is visible and selectable.
- The standalone normalizer converts a real external OHLCV feed into `ict-engine` candle JSON.
- `ict-engine analyze` directly consumes the normalized external JSON.
- Auto-Quant synthetic OHLCV prepare consumes the normalized external JSON and materializes the expected managed workspace data files.
- The original runtime blockers were repaired in sequence:
  - pair alias normalization (`BTCUSDT_EXT_1H/USD` -> `BTCUSDT/USD`)
  - Feather `date` dtype preservation
  - source-derived timerange instead of stale template range
- The latest AQ runtime smoke now executes successfully and reaches adoption-review `ready_for_external_execution`.

## 2026-05-15 Runtime Repair Packet

Repair summary:
- `src/application/auto_quant/workspace_profile.rs`
  - normalize runtime-only workflow symbols before generating AQ `pair_whitelist`
  - derive `timerange` from the source candle set
- `support/scripts/auto_quant_external/prepare_external.py`
  - preserve datetimelike `date` when writing Feather

Focused verification:
- `cargo test synthetic_ohlcv_pair_alias -- --nocapture`
- `cargo test source_candle_timerange_uses_first_and_last_utc_dates -- --nocapture`
- `python3 -m py_compile support/scripts/auto_quant_external/prepare_external.py support/scripts/auto_quant_external/tests/test_prepare_external.py`
- `uv run --with pandas --with pyarrow python -m unittest support/scripts/auto_quant_external/tests/test_prepare_external.py -v`
- `python3 -m py_compile support/scripts/research/external_history_adoption.py support/scripts/research/tests/test_external_history_adoption.py`
- `python3 -m unittest support/scripts/research/tests/test_external_history_adoption.py -v`

Latest runtime smoke:
- Root: `/tmp/ict-engine-external-history-smoke-v4`
- Input: `/tmp/ict-engine-external-history-smoke-v4/btcusdt.binance.1h.normalized.json`
- AQ state: `/tmp/ict-engine-external-history-smoke-v4/state-factor`
- `config.tomac.json` now contains:
  - `pair_whitelist=["BTCUSDT/USD"]`
  - source-derived `timerange` covering the real 2026-05 sample window
- `run_tomac.py` result:
  - `Done: 1 succeeded, 0 failed.`
  - `pair=BTCUSDT/USD`
  - `trade_count=0`
  - backtest window loaded and indicators/backtest loop executed successfully
- `auto-quant-adoption-review` result:
  - `review_status=ready_for_external_execution`
  - `review_summary=handoff is ready for Auto-Quant execution and candidate export`

## Consumer Command Helper

New helper:
- `support/scripts/research/external_history_adoption.py`

Purpose:
- Build a token-friendly local adoption bundle for an opt-in external-history lane.
- Emit `suggested_commands.sh` so the user can choose whether to run
  `workflow-status`, `analyze`, `factor-research`, `auto-quant-prepare`, and
  `auto-quant-adoption-review` with the selected profile.
- Keep zero-config defaults unchanged by staying outside the Rust CLI mainline.

Example real run:
- `python3 support/scripts/research/external_history_adoption.py --repo-root . --market NQ --profile thrill3r_nq_external_history_v1 --symbol BTCUSDT_EXT_1H_LONG --state-dir /tmp/ict-engine-external-history-adoption-v2 --input 1h=/tmp/ict-engine-external-history-smoke-v5/btcusdt.binance.1h.1000.normalized.json --input 4h=/tmp/ict-engine-external-history-smoke-v5/btcusdt.binance.1h.1000.normalized.json --input 1d=/tmp/ict-engine-external-history-smoke-v5/btcusdt.binance.1h.1000.normalized.json --output-dir /tmp/ict-engine-external-history-adoption-v2`

Artifacts:
- `/tmp/ict-engine-external-history-adoption-v2/external_history_adoption_bundle.json`
- `/tmp/ict-engine-external-history-adoption-v2/suggested_commands.sh`

## 2026-05-15 Longer-Window Packet

Run root:
- `/tmp/ict-engine-external-history-smoke-v5`

Input:
- Binance public BTCUSDT `1h` JSON, `limit=1000`
- normalized output:
  `/tmp/ict-engine-external-history-smoke-v5/btcusdt.binance.1h.1000.normalized.json`

Commands run:
- `cargo run --quiet -- factor-research --symbol BTCUSDT_EXT_1H_LONG --data /tmp/ict-engine-external-history-smoke-v5/btcusdt.binance.1h.1000.normalized.json --objective regime_conditioned_profitability --backend auto-quant --auto-quant-profile synthetic_ohlcv --state-dir /tmp/ict-engine-external-history-smoke-v5/state-factor --human`
- `cargo run --quiet -- auto-quant-prepare --state-dir /tmp/ict-engine-external-history-smoke-v5/state-factor`
- `uv run --with ta-lib --with freqtrade /tmp/ict-engine-external-history-smoke-v5/state-factor/.deps/auto-quant/run_tomac.py`
- `cargo run --quiet -- auto-quant-adoption-review --symbol BTCUSDT_EXT_1H_LONG --state-dir /tmp/ict-engine-external-history-smoke-v5/state-factor`

Outcome:
- `pair=BTCUSDT/USD`
- `trade_count=5`
- `total_profit_pct=1.12`
- `sharpe=0.6437`
- `win_rate_pct=80.0`
- `profit_factor=1.5635`
- `review_status=ready_for_external_execution`
