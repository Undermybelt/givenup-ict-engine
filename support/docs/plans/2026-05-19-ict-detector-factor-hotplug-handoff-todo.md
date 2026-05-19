# 2026-05-19 ICT detector factor hotplug handoff TODO

## Scope

Detector/classification factors only. This is not a profitability-factor,
Auto-Quant, or trading-promotion lane.

Primary user corrections preserved:
- Gap/FVG family must include ICT delivery-gap `volume_imbalance`, not only
  rolling volume-spike anomaly.
- Liquidity family must expose `smooth` / `jagged` / `mixed` and sweep
  `clean` / `dirty` / `mixed` as explicit detector evidence.
- Default path must stay zero-config, consumer-usable, token-friendly, and free
  of maintainer-local data.
- User-specific or richer data must be hot-pluggable and opt-in.

## Done

- Confirmed existing core detector work from the prior slice:
  - `src/ict/volume_imbalance.rs` has ICT delivery-gap
    `VolumeImbalanceGap` detection, separate from rolling z-score
    `VolumeImbalance`.
  - `src/ict/liquidity.rs` has typed `smooth` / `jagged` / `mixed`
    liquidity pool texture and `clean` / `dirty` / `mixed` sweep quality.
  - `src/ict/ob.rs` owns typed order-block variant classification.
- Added consumer/runtime surfacing for ICT delivery-gap volume imbalance:
  - `PriceActionSection.volume_imbalance_gap`
  - `VolumeImbalanceGapEvidence`
  - `VolumeImbalanceGapRuntimeEvidence`
  - `AnalyzeRunRecord.volume_imbalance_gap`
  - `WorkflowPhaseSnapshot.volume_imbalance_gap`
- Wired zero-config analyze output to detect the nearest active unfilled
  delivery-gap VI from ordinary MTF candles:
  - compact human field: `volume_imbalance_gap=<active|filled|none>`
  - compact band field: `vi_gap=(bottom-top)`
  - direction/fill metadata: `vi_direction`, `vi_start_bar`, `vi_filled`
- Kept personal/private enrichment out of default detector code. No broker,
  watchlist, local file, API key, or maintainer path is read by the detector.
- Reclaimed verification space only by deleting rebuildable cargo incremental
  cache:
  - removed `.local-artifacts/cargo-target/debug/incremental`
  - reran expensive tests with `CARGO_INCREMENTAL=0` to avoid re-polluting the
    disk with large incremental caches.
- Added the first opt-in detector hotplug context carrier:
  - `DetectorHotplugContext` in `src/factors/hotplug.rs`
  - optional `FactorHotplugConfig.detector_context`
  - fields: `session_label`, `source_profile`, `volume_quality`,
    `symbol_context`, `calendar_context`
  - default remains `None`; detector modules still read no broker, watchlist,
    API key, local file, or maintainer-only path unless a user explicitly points
    `factor_hotplug.yaml` / `ICT_ENGINE_FACTOR_HOTPLUG_CONFIG` at a config.
- Added token-friendly summary behavior for opt-in detector context:
  - `FactorHotplugConfig::summary_line()` reports only which context fields are
    present, not their values.
- Threaded `policy-training-status` / training export factor-hotplug readback
  through that redacted summary in a later narrow slice, staged as only the
  single summary hook plus its regression test despite broad unrelated dirty
  work in `src/application/entry_models/training_export.rs`.
- Threaded `DetectorHotplugContext` into the analyze human/report adapter as an
  opt-in redacted detector-context suffix:
  - default analyze technical summaries are unchanged when no explicit
    hotplug config exists or no detector context is configured.
  - configured values are not printed; only field names are exposed.
  - detector execution remains candle-only; the context is reporting/admission
    metadata only.
- Added typed liquidity sweep quality and equal-high/equal-low liquidity subtype
  classifiers in the core ICT detector layer:
  - `clean`, `dirty`, and `mixed` sweep quality are derived from candle-only
    sweep reclaim behavior, return speed, and ATR-normalized displacement.
  - `equal_high_pool`, `equal_low_pool`, `relative_equal_high`,
    `relative_equal_low` are derived from candle-only pool direction plus
    smooth/jagged/mixed texture.
  - no provider profile, broker data, local path, or personal dataset is read
    by default.

## Verification

- RED observed before implementation:
  - `cargo test --bin ict-engine analyze_human_surface_carries_ict_template_with_price_levels`
  - failed on missing `VolumeImbalanceGapEvidence`,
    `PriceActionSection.volume_imbalance_gap`, and
    `WorkflowPhaseSnapshot.volume_imbalance_gap`.
- GREEN:
  - `cargo test --lib analyze_human_surface_carries_ict_template_with_price_levels`
    passed.
  - `CARGO_INCREMENTAL=0 cargo test --bin ict-engine persist_analyze_run_threads_volume_imbalance_gap_into_latest_analyze_snapshot`
    passed.
  - `CARGO_INCREMENTAL=0 cargo test --lib volume_imbalance` passed.
  - `git diff --check` passed.
- Current continuation GREEN:
  - `cargo test --lib factors::hotplug::tests:: -- --nocapture` passed with 6
    hotplug tests, including default-no-context, explicit YAML load, and
    privacy-preserving summary coverage.
  - Shared target was busy with another active run, so an isolated verification
    was also started with `CARGO_TARGET_DIR=/tmp/ict-engine-target-hotplug-context
    CARGO_INCREMENTAL=0 cargo test --lib factors::hotplug::tests:: -- --nocapture`.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-training-hotplug CARGO_INCREMENTAL=0 cargo test --lib policy_training_status_redacts_opt_in_detector_hotplug_context_values -- --nocapture`
    passed, proving policy-training-status exposes opt-in detector context field
    names without leaking configured values.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-analyze-hotplug CARGO_INCREMENTAL=0 cargo test --lib detector_hotplug_context_adapter_ -- --nocapture`
    passed, proving the analyze report adapter appends redacted context only
    when an opt-in detector context is present.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-liquidity-subtype CARGO_INCREMENTAL=0 cargo test --lib liquidity_pool_texture -- --nocapture`
    passed, proving smooth/jagged liquidity pools receive equal/relative equal
    high-low subtype labels.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-liquidity-core CARGO_INCREMENTAL=0 cargo test --lib liquidity_pool_texture -- --nocapture`
    passed for the staged core classifier slice.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-liquidity-core CARGO_INCREMENTAL=0 cargo test --lib liquidity_sweep_quality -- --nocapture`
    passed for the staged core classifier slice.
  - `rustfmt --edition 2021 --check src/types.rs src/ict/liquidity.rs` passed.
  - `git diff --cached --check` passed.
  - Cached privacy grep for private paths, fixed IPs, obvious credentials, and
    broker identifiers returned no matches.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-liquidity-subtype CARGO_INCREMENTAL=0 cargo test --lib analyze_human_surface_carries_ict_template_with_price_levels -- --nocapture`
    passed, proving the human technical summary carries
    `liquidity_pool_subtype`.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-liquidity-subtype CARGO_INCREMENTAL=0 cargo test --lib target_export_binds_liquidity_texture_runtime_context_to_rooted_branch -- --nocapture`
    passed, proving the structural playbook target still binds liquidity
    texture runtime context after subtype expansion.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-liquidity-subtype CARGO_INCREMENTAL=0 cargo test --bin ict-engine persist_analyze_run_threads_liquidity_pool_texture_into_latest_analyze_snapshot -- --nocapture`
    passed, proving subtype survives analyze-run persistence.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-liquidity-subtype CARGO_INCREMENTAL=0 cargo test --bin ict-engine analyze_snapshot_maps_liquidity_pool_texture_runtime_evidence -- --nocapture`
    passed, proving subtype survives workflow snapshot mapping.
- Residual formatting note:
  - `CARGO_INCREMENTAL=0 cargo fmt --check` currently fails on pre-existing
    unrelated formatting in
    `src/application/orchestration/execution_tree.rs:1173`.
  - This slice did not run full `cargo fmt` because that would edit unrelated
    dirty work.

## Next

1. Add gap/OB mitigation percentage:
   `mitigation_pct`, `failed_mitigation`, and `partial_fill_state` for FVG,
   VI gap, and OB variants.
2. Isolate the already-started runtime/reporting surfacing for
   `liquidity_pool_subtype`, `liquidity_sweep_quality`, and
   `volume_imbalance_gap` from unrelated PDA/path-ranker work before committing
   the next slice. Current worktree has useful detector plumbing, but `main.rs`,
   `analyze_shared.rs`, and `structural_playbook.rs` contain mixed hunks that
   must not be staged whole-file.
3. If this evidence is used by Auto-Quant later, keep it as opt-in feature
   columns or a selected detector bundle. Do not make personal data or richer
   provider context a default runtime dependency.

## Not Yet

- No trading promotion was attempted from this detector slice.
- No Board B downstream chain was run.
- Committed detector hotplug context and redacted policy-training-status
  readback as narrow slices (`b9a41f6a`, `feb5575c`). The repo still has a broad
  dirty worktree from other lanes, so future commits must continue staging only
  coherent hunk/path sets.

Last updated: 2026-05-19 04:28:00 +0800.
Last updated: 2026-05-19 11:02:00 +0800.
