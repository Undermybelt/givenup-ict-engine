# Board B Bear BBN Label Support v1

- Decision: `bear_bbn_label_gap_repaired`
- Source branch: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-chain/regime-bundles/bear_regime_consumer_bundle_v1.json`
- Target branch path: `Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12`
- Unit evidence: `cargo test --test regime_consumer_bundle_adapter bear_relief_bundle_applies_to_bear_pre_bayes_soft_evidence` exited `0`
- Runtime evidence: `ict-engine analyze --demo --apply-regime-bundle-bbn-soft-evidence` against the Bear bundle exited `0`
- BBN evidence result: `regime_bundle_bbn_evidence_applied=strength:moderate label:primary::BearReliefCarry`
- Filtered BBN market regime: `bear`
- Soft market regime distribution: `bear=0.65`, `bull=0.175`, `range=0.175`

## Remaining Blocker

This retires the Bear `no_supported_label` blocker only. The B5 promotion blocker remains the structural path-ranking / execution-tree path-id contract: ict-engine still needs exact Board B `regime_profit_branch_path` values, or an explicit bijection from structural runtime path ids to those branch paths, before `220646` can be promoted.

## Artifacts

- Test output: `docs/experiments/actionable-regime-confidence/runs/20260511T223933-codex-board-b-bear-bbn-label-support-v1/command-output/cargo_test_bear_relief_bundle.out`
- Runtime output: `docs/experiments/actionable-regime-confidence/runs/20260511T223933-codex-board-b-bear-bbn-label-support-v1/command-output/analyze_demo_bear_bundle.out`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T223933-codex-board-b-bear-bbn-label-support-v1/checks/bear_bbn_label_support_v1_assertions.out`
