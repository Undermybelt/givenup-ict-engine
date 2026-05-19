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
- Isolated and staged the runtime/reporting surfacing slice from a clean
  temporary worktree so unrelated PDA/path-ranker hunks in the dirty checkout
  stayed out of the commit:
  - `PriceActionSection` now carries `liquidity_sweep_quality` and
    `volume_imbalance_gap` alongside `liquidity_pool_texture.subtype`.
  - `analyze` builds those detector fields from ordinary candle data.
  - analyze-run persistence and workflow snapshot mapping carry the runtime
    evidence forward.
  - compact human output includes `liquidity_pool_subtype`,
    `sweep_quality/clean_or_dirty`, `displacement_atr`, `return_bars`,
    `close_reclaim`, and VI delivery-gap state fields.
- Added candle-only mitigation/fill-state evidence for the gap/OB detector
  slice from a clean temporary worktree:
  - shared price-band mitigation classifier derives `mitigation_pct`,
    `failed_mitigation`, and `partial_fill_state` from ordinary candles only.
  - VI delivery gaps carry `vi_mitigation_pct`, `vi_failed_mitigation`, and
    `vi_partial_fill_state` through human output, analyze-run persistence, and
    workflow snapshot mapping.
  - nearest open FVG carries compact `fvg_mitigation_pct`,
    `fvg_failed_mitigation`, and `fvg_partial_fill_state` on the analyze human
    surface.
  - OB variants carry `ob_mitigation_pct`, `ob_failed_mitigation`, and
    `ob_partial_fill_state` through human output, analyze-run persistence, and
    workflow snapshot mapping.
  - no provider profile, broker data, local path, API key, or personal dataset
    is read by default.
- Added the first opt-in detector GA/search feature bundle carrier for later
  Auto-Quant or genetic-optimizer use, without adding NextTrade or any external
  runtime dependency:
  - `DetectorGaFeatureBundle` in `src/factors/hotplug.rs`
  - optional `FactorHotplugConfig.detector_ga_bundle`
  - fields: `bundle_id`, `target_consumer`, `selected_fields`,
    `optimizer_objectives`, `validation_windows`
  - default remains `None`; no detector, Auto-Quant, broker, local path, or
    personal data source is read unless a user explicitly points
    `factor_hotplug.yaml` / `ICT_ENGINE_FACTOR_HOTPLUG_CONFIG` at a config.
  - summary is token-friendly and redacted: it reports bundle presence,
    sanitized target name, sorted selected field names, sorted objective names,
    and validation-window count, not configured path/value contents.
  - intended initial bundle fields are the newly surfaced candle-only detector
    columns such as `vi_mitigation_pct`, `fvg_mitigation_pct`,
    `ob_mitigation_pct`, `liquidity_pool_subtype`, and `sweep_quality`.
- Added a reusable opt-in detector GA/search manifest exporter without touching
  the dirty CLI command surface:
  - `persist_detector_ga_feature_manifest(state_dir)` loads only explicit
    `factor_hotplug.yaml` / `ICT_ENGINE_FACTOR_HOTPLUG_CONFIG` input.
  - absent config or absent `detector_ga_bundle` is a no-op and creates no
    `auto-quant/` output.
  - explicit bundles write
    `<state-dir>/auto-quant/ga_optimizer/detector_feature_manifest.json`.
  - manifest schema is `ict_detector_ga_feature_manifest_v1` and carries only
    compact public tokens: `bundle_id`, `target_consumer`, `selected_fields`,
    `optimizer_objectives`, `validation_windows`, plus warnings for dropped
    duplicate/unsafe tokens.
  - path-like or private-looking validation-window values are dropped from the
    manifest, preserving the public/consumer-safe default.
- Added a sanitized opt-in consumer example for the detector GA/search bundle:
  - `support/examples/factor_hotplug/detector-ga-search-v1.yaml`
  - `support/examples/factor_hotplug/README.md` documents explicit opt-in
    usage by copying the example into `<state-dir>/factor_hotplug.yaml` or by
    setting `ICT_ENGINE_FACTOR_HOTPLUG_CONFIG` for a single run.
  - all factor families remain enabled by default in the example.
  - selected detector fields are limited to the candle-only columns surfaced in
    this lane: `vi_mitigation_pct`, `fvg_mitigation_pct`,
    `ob_mitigation_pct`, `liquidity_pool_subtype`, and `sweep_quality`.
  - optimizer objectives are generic admission/search objectives:
    `regime_conditioned_win_rate` and `cost_adjusted_expectancy`.
  - validation windows are public compact labels only; no local path, broker,
    credential marker, account id, or personal dataset appears in the example.
  - README text keeps docs as examples only; runtime still consumes typed YAML
    config/helper APIs and does not parse markdown.
- Added a compact reusable detector GA/search manifest prepare status helper:
  - `prepare_detector_ga_feature_manifest(state_dir)` remains opt-in and
    zero-config safe.
  - absent config reports `config_absent` and writes nothing.
  - config present without `detector_ga_bundle` reports
    `detector_ga_bundle_absent` and writes nothing.
  - explicit bundles write the same sanitized manifest under
    `<state-dir>/auto-quant/ga_optimizer/` and return only compact counts:
    schema version, path, selected-field count, objective count,
    validation-window count, and warning count.
  - the status helper does not echo configured detector field values, objective
    names, validation-window labels, broker data, local paths, or credentials.

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
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-runtime-real CARGO_INCREMENTAL=0 cargo test --lib analyze_human_surface_carries_ict_template_with_price_levels -- --nocapture`
    passed, proving the real-checkout staged runtime/reporting slice surfaces
    the detector fields in the compact human summary.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-runtime-real CARGO_INCREMENTAL=0 cargo test --bin ict-engine analyze_snapshot_maps_liquidity_pool_texture_runtime_evidence -- --nocapture`
    passed, proving the real-checkout staged runtime/reporting slice maps the
    detector runtime evidence into workflow snapshots.
  - `rustfmt --edition 2021 --check` passed on the staged detector runtime files:
    `src/analyze_sections.rs`, `src/analyze_shared.rs`,
    `src/application/reporting/analyze_output.rs`, `src/main.rs`,
    `src/state/types.rs`, `src/state/persistence.rs`, and
    `src/workflow_snapshot_runtime.rs`.
  - Cached diff checks passed and a cached scan confirmed the staged slice has
    no PDA/path-ranker terms or private-path/credential additions.
- Current mitigation/fill-state continuation GREEN:
  - RED first: `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-mitigation-red CARGO_INCREMENTAL=0 cargo test --bin ict-engine price_band_mitigation_classifies -- --nocapture`
    failed because `classify_price_band_mitigation` did not exist.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-mitigation-green CARGO_INCREMENTAL=0 cargo test --bin ict-engine price_band_mitigation_classifies -- --nocapture`
    passed, proving partial and failed mitigation states are classified from
    candle-only price-band interaction.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-mitigation-green CARGO_INCREMENTAL=0 cargo test --lib analyze_human_surface_carries_ict_template_with_price_levels -- --nocapture`
    passed, proving compact human output carries VI/FVG/OB mitigation fields.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-mitigation-green CARGO_INCREMENTAL=0 cargo test --bin ict-engine analyze_snapshot_maps_liquidity_pool_texture_runtime_evidence -- --nocapture`
    passed, proving runtime snapshot mapping carries VI and OB mitigation
    fields alongside existing detector evidence.
- Current detector GA/search bundle continuation GREEN:
  - RED first: `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-ga-red CARGO_INCREMENTAL=0 cargo test --lib factors::hotplug::tests:: -- --nocapture`
    failed on missing `DetectorGaFeatureBundle` and
    `FactorHotplugConfig.detector_ga_bundle`, proving the tests were guarding a
    new opt-in schema contract.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-ga-green CARGO_INCREMENTAL=0 cargo test --lib factors::hotplug::tests:: -- --nocapture`
    passed with 9 hotplug tests, proving default-off behavior, explicit YAML
    load, and redacted token-friendly summary for the detector GA/search bundle.
- Current detector GA/search manifest continuation GREEN:
  - RED first: `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-ga-manifest-red CARGO_INCREMENTAL=0 cargo test --lib factors::hotplug::tests::test_detector_ga_manifest_export -- --nocapture`
    failed on missing `persist_detector_ga_feature_manifest`, proving the tests
    guarded a new artifact export behavior.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-ga-manifest-green CARGO_INCREMENTAL=0 cargo test --lib factors::hotplug::tests::test_detector_ga_manifest_export -- --nocapture`
    passed with 2 tests, proving no-op default behavior and sanitized manifest
    export to `<state-dir>/auto-quant/ga_optimizer/` for explicit bundles.
- Current sanitized example continuation GREEN:
  - RED first: `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-ga-example-red CARGO_INCREMENTAL=0 cargo test --lib factors::hotplug::tests::test_sanitized_example_detector_ga_bundle_parses_and_exports_manifest -- --nocapture`
    failed because `support/examples/factor_hotplug/detector-ga-search-v1.yaml`
    did not exist, proving the test guarded a real consumer-facing artifact.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-ga-example-green CARGO_INCREMENTAL=0 cargo test --lib factors::hotplug::tests::test_sanitized_example_detector_ga_bundle_parses_and_exports_manifest -- --nocapture`
    passed, proving the sanitized example parses, exports a detector GA/search
    manifest, and contains no `/Users` or credential-marker strings in the
    summary or manifest.
- Current detector GA/search prepare-status continuation GREEN:
  - RED first: `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-ga-status-red CARGO_INCREMENTAL=0 cargo test --lib factors::hotplug::tests::test_detector_ga_manifest_export_status_is_compact_and_noop_safe -- --nocapture`
    failed on missing `prepare_detector_ga_feature_manifest`, proving the test
    guarded a new reusable helper rather than existing manifest persistence.
  - Initial GREEN exposed a test setup mismatch: absent config correctly
    returned `config_absent`, while the test had expected
    `detector_ga_bundle_absent`. The test was tightened to cover both no-op
    states explicitly.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-target-detector-ga-status-green CARGO_INCREMENTAL=0 cargo test --lib factors::hotplug::tests::test_detector_ga_manifest_export_status_is_compact_and_noop_safe -- --nocapture`
    passed, proving the helper is no-op safe, distinguishes absent config from
    absent bundle, exports explicit bundles, returns only compact counts, and
    does not expose unsafe validation-window values in the debug/status surface.
- Current example README continuation:
  - Added `support/examples/factor_hotplug/README.md` as a consumer-facing
    opt-in usage note only. It contains no maintainer-local path, broker id,
    account id, token, secret, or API key, and it points generated state to
    `/tmp/ict-engine-detector-ga-demo`.
- Residual formatting note:
  - `CARGO_INCREMENTAL=0 cargo fmt --check` currently fails on pre-existing
    unrelated formatting in
    `src/application/orchestration/execution_tree.rs:1173`.
  - This slice did not run full `cargo fmt` because that would edit unrelated
    dirty work.

## Next

1. Consider a follow-up `auto-quant-ga-prepare` command wrapper around the new
   prepare-status helper once the dirty CLI command files can be touched safely.
   The wrapper should print only the manifest path, schema, field count,
   objective count, validation-window count, warning count, and no-op reason.
2. If command files remain dirty, prefer a clean temporary worktree for the
   command wrapper so unrelated `main.rs` / `auto_quant_command.rs` work stays
   out of the slice.
3. Keep all GA/search results as candidate/admission evidence. Do not allow a
   GA bundle alone to promote trading execution without the existing Pre-Bayes,
   BBN, path-ranker, cost/slippage, and execution-tree gates.

## Not Yet

- No trading promotion was attempted from this detector slice.
- No Board B downstream chain was run.
- Committed detector hotplug context and redacted policy-training-status
  readback as narrow slices (`b9a41f6a`, `feb5575c`). The repo still has a broad
  dirty worktree from other lanes, so future commits must continue staging only
  coherent hunk/path sets.

Last updated: 2026-05-19 04:28:00 +0800.
Last updated: 2026-05-19 11:02:00 +0800.
Last updated: 2026-05-19 11:34:00 +0800.
Last updated: 2026-05-20 00:00:00 +0800.
Last updated: 2026-05-20 00:33:00 +0800.
Last updated: 2026-05-20 00:49:00 +0800.
Last updated: 2026-05-20 01:08:00 +0800.
Last updated: 2026-05-20 01:42:00 +0800.
Last updated: 2026-05-20 02:31:00 +0800.
