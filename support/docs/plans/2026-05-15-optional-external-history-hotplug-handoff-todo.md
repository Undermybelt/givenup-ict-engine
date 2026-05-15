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
