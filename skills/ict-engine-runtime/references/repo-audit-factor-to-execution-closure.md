# ICT-Engine repo audit: factor iteration -> execution advice closure

Use after a whole-repo audit asks whether factor iteration, filters, regime, BBN evidence, CatBoost/path ranking, execution tree, and final advice are actually connected.

## Audit method

1. Read `AGENTS.md` first; it maps factor families and key source paths.
2. Inspect the live chain, not only docs:
   - factor definitions/registry/engine
   - factor research/backtest runtimes
   - market_state/filter/regime modules
   - BBN/Pre-Bayes evidence conversion
   - structural path ranker/CatBoost runtime
   - execution_tree trace and workflow/reporting output
3. Run `git status --short` before validation. If worktree is dirty, identify whether compile failures come from pre-existing edits.
4. Validate with `cargo check` before claiming a closed loop. If `cargo check` fails, treat test results as blocked until compile is restored.
5. For `cargo test`, pass one filter at a time, e.g. `cargo test execution_tree -- --nocapture`; do not pass multiple bare filters.

## Findings to check explicitly

### Compile gate
- `PolicyTrainingStatusSurface` field additions must update every struct initializer.
- A dirty worktree can create apparent repo failures; do not silently fix unrelated edits.

### Factor chain
- 8 families may be defined and registered, but runtime parity still needs checking.
- `FactorRegistry::default()` call sites with `state_dir` should apply `FactorHotplugConfig`.
- Backtest runtime can diverge from analyze if it omits hotplug or auxiliary evidence.
- Analyze can have multi-timeframe data but still fail to inject `h4_events/d1_events/w1_events` into `FactorContext`.

### market_state / regime / BBN
- `MarketStateClassifier` can produce `primary_regime` and `secondary_regime` while the main analyze chain still uses native frame/HMM labels instead.
- `market_state/evidence_mapping.rs` node names may not match trading BBN nodes.
- `secondary_regime` can be defined but not inserted into evidence.
- `pass_to_bbn=false` must be verified in the main chain; recording it is not the same as blocking inference.
- Evidence provenance requires more than `HashMap<NodeId, EvidenceType>` if the user asks for each node and evidence source.
- Watch for canonical BBN/report paths that rebuild pseudo filters or drop soft evidence.

### CatBoost / path ranker / execution tree
- External scores can affect structural path ranking without entering `execution_tree_trace.json`.
- `model_family=catboost` registration does not imply Rust can directly load/infer a CatBoost model.
- Check whether path ranker raw/calibrated/lower-bound scores appear in:
  - structural path runtime summary
  - workflow_status human/JSON trace
  - execution_tree input/lineage
  - final recommended_command / human next action
- If CatBoost is only visible in workflow_status and not in execution_tree trace, the runtime skill's trace requirement is not met.

## Report shape

Return outcome first, then evidence by stage:
- compile/validation status
- factor iteration
- filters and regime classification
- BBN/Pre-Bayes evidence
- CatBoost/path ranking
- execution tree and final advice
- highest-priority fixes

Keep file paths with line numbers. State whether files were modified. Do not claim a closed loop if `cargo check` is failing.