# Runtime closure implementation notes

Use when converting an ict-engine closure audit finding into code changes across analyze, BBN, path-ranker, and execution-tree surfaces.

## Proven minimal closure pattern

### 1. Compile blockers first

If `PolicyTrainingStatusSurface` gets a new field, every direct struct initializer must fill it, or `cargo check` blocks the rest of the audit. For hotplug summaries, prefer a single computed string in `policy_training_status()`:

- no config: `Factor hotplug: config=absent all_default_enabled`
- config present: list disabled families
- invalid config: preserve error text in the summary

### 2. market_state must become consumed evidence, not sidecar code

A minimal closure path is:

1. `MarketStateClassifier::new().classify(native_ltf)` in analyze.
2. Convert to existing trading BBN node labels instead of inventing unconsumed nodes:
   - `RangeConsolidation | ExtremeStress | ReversalBrewing` -> `market_regime=range`
   - `HighLiquidity` -> `liquidity_context=favorable`
   - `NormalLiquidity` -> `neutral`
   - `ThinLiquidity` -> `hostile`
3. Store provenance in all relevant surfaces:
   - `AnalyzeSupporting.market_state_evidence`
   - `AnalyzeRunRecord.market_state_evidence`
   - `WorkflowPhaseSnapshot.market_state_evidence`
   - `PreBayesEvidenceFilter.rationale`
   - `PreBayesEvidenceFilter.evidence_assignments`
4. Pass `market_state_lineage` into `ExecutionTreeInput` and append it to `split_reason_lineage`.

This proves primary/secondary regime is consumed by analyze -> Pre-Bayes/BBN -> workflow/run state -> execution-tree trace.

### 3. `pass_to_bbn=false` must neutralize inference

A recorded `pass_to_bbn=false` is not enough. In `trade_evidence_from_pre_bayes_filter`, use soft distributions when either:

```rust
filter.uses_soft_evidence || !filter.pass_to_bbn
```

This prevents observe-only evidence from falling back to hard evidence.

### 4. Path-ranker/CatBoost trace closure

`structural_playbook` may already apply external scores to candidate paths, but execution-tree trace still needs a lineage surface. Minimal pattern:

1. Add `path_ranker_lineage: Option<&[String]>` to `ExecutionTreeInput`.
2. Append `path_ranker=<line>` to `split_reason_lineage`.
3. In analyze, derive lineage from `policy_training_status(state_dir, symbol, None)`:
   - `structural_path_ranking_runtime_summary`
   - `structural_path_ranking_validation_summary`
   - hotplug summary if available
4. Add `path_ranker_lineage: None` to all tests and reflection bundle constructors.

Warning: calling `policy_training_status` inside analyze can make `cargo check` slow only if the edit causes wider recompilation; if runtime concerns arise, replace with a lighter helper that loads only the structural path ranking target summary.

### 5. Backtest/analyze parity

When `FactorRegistry::default()` is used in a runtime path with `state_dir` available, immediately apply hotplug:

```rust
let mut registry = FactorRegistry::default();
FactorHotplugConfig::apply_to_registry_if_present(state_dir, &mut registry);
```

For analyze parity with factor research/backtest, pass H4/D1/W1 PDA events into `FactorContext` when native frames are available:

```rust
let h4_events = native_h4.map(|c| build_pda_timeline(c, &compute_atr(c, 14)));
let d1_events = native_d1.map(|c| build_pda_timeline(c, &compute_atr(c, 14)));
let w1_events = native_d1.map(|c| {
    let weekly = aggregate_daily_candles_to_weekly(c);
    build_pda_timeline(&weekly, &compute_atr(&weekly, 14))
});
```

Then set `h4_events/d1_events/w1_events` on `FactorContext`.

## Verification commands

Use separate cargo test filters; cargo accepts only one test name filter before `--`:

```bash
cargo check
cargo test execution_tree -- --nocapture
cargo test market_state -- --nocapture
cargo test evidence -- --nocapture
cargo test structural_path -- --nocapture
```

If `cargo check` is slow after broad schema edits, run once in background and poll, but do not claim verification until exit status is known.

## Common compile misses after schema edits

- New `ExecutionTreeInput` field -> every test and reflection constructor needs `None`.
- New `WorkflowPhaseSnapshot` field -> every phase builder needs an initializer.
- New `AnalyzeRunRecord` field -> `Default` and persist path both need updates.
- New `AnalyzeSupporting` field -> main analyze constructor must fill it.
