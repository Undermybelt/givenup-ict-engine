# 2026-05-21 Futures Cost Profile Hotplug Handoff TODO

## Objective

Replace blanket fixed-bps futures friction with instrument-aware cost profiles in ict-engine infrastructure, then re-evaluate Tomac ES/YM/NQ factor evidence using realistic futures tick value, spread/slippage, and commission assumptions.

## Constraints

- Zero-config consumers must get generic public defaults without private paths.
- Maintainer-local Tomac data remains opt-in/hot-pluggable; no `/Users/.../Downloads` path belongs in default runtime output.
- Gate standards do not get lowered: cost-surviving density is only Gate 1; practical promotion still requires same-root downstream evidence, direction consistency, `transition_hazard < 0.60`, `pda_hybrid_alignment=true`, and `execution_readiness >= 0.65`.
- Generated state stays in `/tmp` or compact run packets; do not pollute the repo with large data.
- Preserve unrelated dirty worktree changes.

## Done

- Routed through `sd/ict-engi-fact-rese-muta` and read repo `AGENT.md`.
- Confirmed active Tomac/Auto-Quant processes are still running; no takeover or kill was performed.
- Identified the fixed futures cost bug in `run_tomac_index_futures_clean_aq_v1.py`: Gate 1 currently uses fixed `5bps/side` via `gross - trades * bps * 0.02`.
- Added RED tests for:
  - Rust `FuturesCostCatalog` default profiles for ES/NQ/YM.
  - Instrument-aware futures round-trip cost percent below naive fixed 5bps/side stress.
  - Token-friendly unknown-symbol error.
  - Tomac scoring fields `cost_profile_id`, `instrument_round_trip_cost_pct`, `instrument_cost_total_profit_pct`, and `survives_instrument_cost`.
- Implemented the first infrastructure slice in `src/application/auto_quant/futures_cost.rs` and exported `FuturesCostCatalog` / `FuturesCostProfile`.
- Added zero-config consumer CLI surface `auto-quant-futures-cost`:
  - known symbols/contracts print instrument-specific cost assumptions in `json`, `compact`, or `human` format.
  - `--profile <json>` hot-plugs user/broker-specific overrides without private defaults.
  - unknown symbols fail with compact `unknown futures cost profile: <ROOT>` error.
- Patched Tomac clean AQ Gate 1 scoring to use `survives_instrument_cost` for futures, keeping fixed 0/1/2/5bps columns as diagnostics only.
- Expanded default profile coverage across equity index, metals, energy, rates, FX, and grains, and added JSON hotplug override support for consumer/user-specific broker profiles.
- Online research note: contract tick ladders are exchange-defined, but total execution cost is broker/account/fee-tier dependent. Infrastructure therefore separates tick value, spread, slippage, broker commission, exchange/clearing fees, and regulatory fees instead of pretending one fixed bps is universally correct.
- Re-scored existing Tomac clean AQ summary CSVs under instrument-aware cost without launching a new long AQ run:
  - artifact: `/tmp/ict-engine-tomac-realistic-futures-cost-rescore-20260521.json`
  - NQ `1m` public rotation remains no-survivor after realistic futures cost.
  - NQ `5m` `tomac_idxfut_clean_nr7_range_expansion_5m_v1` becomes a corrected-cost Gate 1 survivor: `1362` trades, raw `+18.17%`, instrument-cost net `+12.555533%`, profile `CME_NQ_default_v1`.
- Verification:
  - `cargo fmt --check` passed.
  - `python3 -m unittest support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_index_futures_clean_aq.py` passed: `15` tests.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-futures-cost-target cargo test --test auto_quant_futures_cost` passed: `5` tests. Used `/tmp` target dir to avoid the shared repo artifact lock from other active cargo work.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-futures-cost-cli-target cargo test --test provider_neutral_cli auto_quant_futures_cost_cli_is_zero_config_and_token_friendly` passed after RED confirmed the command was missing.

## Next

- Carry NQ `5m` NR7 corrected-cost survivor into exact downstream only after confirming active Tomac/AQ process state and preserving same rooted branch metadata:
  - branch: `RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> tomac_idxfut_clean_nr7_range_expansion_5m_v1`
  - artifact: `/tmp/ict-engine-tomac-realistic-futures-cost-rescore-20260521.json`
  - required verdict: Pre-Bayes/BBN/CatBoost/execution-tree must still fail closed unless exact-root admission, `transition_hazard < 0.60`, `pda_hybrid_alignment=true`, `execution_readiness >= 0.65`, and mature validation rows all pass.
- Wire the Rust `FuturesCostCatalog` into the public Auto-Quant/material cost path when a consumer-facing command needs automated futures cost evaluation inside ranking or Gate 1. Keep maintainer-local Tomac scripts as opt-in research wrappers, not default runtime dependencies.
- Add broader smoke coverage if the CLI output becomes part of provider workflows; current integration coverage proves NQ contract normalization, compact output, no private path leak, and unknown-symbol error.
- If more futures products are requested, extend the catalog by root symbol with exchange tick specs first, then fee/spread/slippage assumptions as overrideable fields. Do not turn one broker's fee tier into a hard-coded universal truth.

## Not Yet

- No downstream Pre-Bayes/BBN/CatBoost/execution-tree replay has been run for the NQ `5m` NR7 corrected-cost survivor yet.
- No public CLI command has been added yet to dump the entire catalog at once; `auto-quant-futures-cost --symbol <root-or-contract> --price <price>` covers one product per query.
- No exchange/broker-specific fee profile is claimed as exact for the maintainer's personal account. Defaults are conservative zero-config assumptions; users can hot-plug JSON overrides.
- Commit `017ed734 feat: add futures cost profiles for auto quant` contains the coherent infra + test slice.

## Active Process Snapshot

- Latest checked active Tomac/AQ slot during continuation:
  - `auto-quant-agent-material-dispatch --symbol BYBIT_BTCUSDT_VOLATILITY_EXPANSION_1M_FULL_LADDER_V1`
  - child: `<local Auto-Quant venv>/python run_tomac.py`
- Treat active `run_tomac.py` children as external work unless their run roots are explicitly adopted. Recheck process state before launching any exact downstream replay.

## Cost Profile Scope

- Default cost profiles are infrastructure assumptions, not trading advice or broker account truth.
- Contract mechanics are per instrument: `tick_size`, `tick_value`, point value, and root symbol matching are separate for ES/MES/NQ/MNQ/YM/MYM/RTY/M2K, metals, energy, rates, FX, and grains.
- Wear/friction is decomposed into `commission_per_contract_side`, `exchange_fees_per_contract_side`, `regulatory_fees_per_contract_side`, `assumed_spread_ticks`, and `assumed_slippage_ticks_per_side`.
- Fixed bps stress columns may remain as diagnostics for cross-asset comparability, but futures Gate 1 truth should use `survives_instrument_cost` or an equivalent instrument-aware profile.
