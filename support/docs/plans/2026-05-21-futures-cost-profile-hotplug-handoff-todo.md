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

## Next

- Implement `src/application/auto_quant/futures_cost.rs` with typed default futures cost profiles.
- Export the helper from `src/application/auto_quant/mod.rs`.
- Patch Tomac clean AQ scoring to gate on `survives_instrument_cost` for futures, while retaining fixed bps columns as diagnostics.
- Carry NQ `5m` NR7 corrected-cost survivor into exact downstream only after confirming the active Tomac/AQ process state and preserving same rooted branch metadata.

## Not Yet

- No downstream Pre-Bayes/BBN/CatBoost/execution-tree replay has been earned under the corrected cost model yet.
- No commit yet; wait until the coherent infra + test slice is green.

## Active Process Snapshot

- Short-reversal Tomac run still active at last check:
  - `/private/tmp/ict-engine-tomac-index-futures-short-reversal-1m-20260521T101825+0800`
  - compact packet: `support/docs/experiments/actionable-regime-confidence/runs/20260521T101825+0800-codex-tomac-index-futures-short-reversal-1m-v1`
- Additional `run_tomac.py` children are active from other lanes. Treat them as external work unless their run roots are explicitly adopted.
