# Regime consumer auxiliary evidence wiring

Use this when Board A regime-confidence work needs to prove paper-backed sidecar evidence (HV/IV/VIX/VVIX, VRP/NQ context, volatility context) reaches the main runtime chain, not just a sidecar report.

## Durable pattern

Stable regime taxonomy is not enough; auxiliary evidence must be visible at each downstream surface:

1. Sidecar bundle
   - `regime_consumer_bundle.json`
   - `consumer_hints.user_vrp_nq_context`
   - expected keys:
     - `qqq_hv_level`
     - `nq_vs_200d_pct`
     - `vix3m_level`
     - `qqq_hv_pct_rank_252`
     - `vvix_over_vix`

2. BBN / pre-Bayes
   - Map to machine assignments:
     - `regime_aux_qqq_hv_level`
     - `regime_aux_nq_vs_200d_pct`
     - `regime_aux_vix3m_level`
     - `regime_aux_qqq_hv_pct_rank_252`
     - `regime_aux_vvix_over_vix`
   - Mirror read-only diagnostics as `read_only_regime_aux_*`.
   - Do not claim applied BBN influence unless `--apply-regime-bundle-bbn-soft-evidence` is explicit and the soft-evidence application status is `applied`.

3. Structural path-ranking / CatBoost target
   - Add the same five fields as stable optional numeric columns on `StructuralPathRankingTargetRow`.
   - Include them in CSV rendering and `structural_path_ranking_trainer_manifest().feature_columns`.
   - Fill from `WorkflowSnapshot.latest_analyze.pre_bayes_filtered_assignments`, not from markdown plans.

4. Execution tree trace
   - Push `regime_aux_context=<key>=<value>` into path-ranker lineage before scoring.
   - Ensure the execution tree lineage cap is large enough that aux lines do not evict CatBoost/ranker score lines.

## Verification shape

Target regression should prove all three surfaces in one run:

- BBN assignment contains e.g. `regime_aux_qqq_hv_level=18.250000`.
- Read-only assignment contains e.g. `read_only_regime_aux_vvix_over_vix=5.100000`.
- `execution_tree_trace.json` contains `regime_aux_context=regime_aux_qqq_hv_level=18.250000`.
- `structural_path_ranking_target.csv` contains the aux column name and value.

Commands used in the successful slice:

```bash
cargo fmt --check
cargo test test_analyze_command_persists_regime_bundle_branch_path_on_execution_candidate -- --nocapture
git diff --check -- <touched-files>
```

## Pitfalls

- Do not add new regime labels just to carry auxiliary evidence. Wire evidence into BBN/target/trace fields.
- Do not treat sidecar coverage as promotion. Board A still needs provider-backed cross-market/cross-period 95% validation.
- Do not read Board A markdown from runtime. Use bundle JSON, workflow state, target artifacts, and execution trace.
- In a multi-agent worktree, patch only the slice you own and preserve unrelated dirty files.
