# Execution-Candidate Branch Path Persistence - 2026-05-24

When a same-root execution-tree admission materializes an actionable
`execution_candidate.json`, the candidate artifact itself must preserve the
canonical regime-root branch identity. Do not rely only on
`execution_tree_trace.json` or `workflow_snapshot.json` for the branch path.

## Symptom

The strict TrendExpansion branch
`TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd`
was repaired enough to persist `actionable=true`, but
`regime_root_metrics_contract_check.py` still failed on
`execution_candidate.json` with:

- `canonical_root_violation:missing_known_main_regime`
- `branch_fields_not_preserved`

The candidate had no `branch_path` or `regime_profit_branch_path`, so the
execution-candidate surface could not prove regime-root parity even though the
execution-tree trace had the admitted same-root `path_id`.

## Fix Pattern

The canonical owner is execution-candidate persistence:

- add backward-compatible candidate fields:
  `branch_path`, `regime_profit_branch_path`, `branch_fields_preserved`;
- populate them from same-root execution-tree admission `path_id` first;
- fall back to report `regime_profit_branch_path` / bundle paths;
- keep practical flags false unless extension gates are complete.

This is a contract repair only. It does not make the branch practical or
trade-usable by itself.

## Evidence

Claim:
`/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260524T095408+0800-codex-execution-candidate-branch-path-persistence-repair.claim`

Runtime replay:
`/tmp/ict-engine-strict-trend-root-branch-path-readback-20260524T095224+0800`

Verification:

- RED: focused Rust test failed with missing candidate branch fields.
- GREEN: strict TrendExpansion same-root candidate tests passed.
- `cargo fmt --check`
- `git diff --check -- src/analyze_shared.rs src/state/types.rs`
- `cargo build -q --bin ict-engine --target-dir .local-artifacts/cargo-target`
- `regime_root_metrics_contract_check.py` returned `contract_ok` on the replayed
  `execution_candidate.json`.

Residual status:

- `promotion_allowed=false`
- `trade_usable=false`
- `extension_complete=false`
- no provider fetch or Auto-Quant dispatch occurred in this repair slice
