# ICT Engine Regime Classifier Sidecar Chain (R2-R17)

Use when continuing high-confidence regime classifier sidecars in `ict-engine`.

## Session Pattern

1. R2 ontology manifest
   - `scripts/research/regime_ontology_manifest.py`
   - `scripts/research/tests/test_regime_ontology_manifest.py`
   - Emits 53 experts: 5 primary, 16 secondary, 24 dimension, 8 transition.
   - Unknown/Neutral style labels are abstain/fallback.

2. R3 feature builder
   - `scripts/research/regime_feature_builder.py`
   - `scripts/research/tests/test_regime_feature_builder.py`
   - Reads OHLCV CSV/JSONL.
   - Optional joins by `timestamp`: auxiliary evidence and MTF PDA events.
   - Pass-through fields: `qqq_hv_level`, `nq_vs_200d_pct`, `vix3m_level`, `qqq_hv_pct_rank_252`, `vvix_over_vix`.
   - Outputs `regime_features.csv` and `feature_quality_report.json`.

3. R4 unsupervised discovery
   - `scripts/research/regime_discovery_cluster.py`
   - `scripts/research/regime_discovery_hmm.py`
   - `scripts/research/tests/test_regime_discovery.py`
   - Evaluates `k=3..12`.
   - Stores BIC/AIC/silhouette/transition_persistence.
   - Maps profile to primary ICT candidates without mutating ontology.
   - Pure-Python deterministic fallback; no sklearn/hmmlearn hard dependency.

4. R5 one-vs-rest expert trainer
   - `scripts/research/regime_expert_trainer.py`
   - `scripts/research/tests/test_regime_expert_trainer.py`
   - Reads R2 ontology plus R3 feature CSV/JSONL.
   - Optional `--cluster-report` / `--hmm-report`; missing optional inputs must not fail.
   - Emits `regime_expert_scores.jsonl` and `regime_expert_training_report.json`.
   - Pure-Python threshold fallback; no sklearn dependency.
   - Precision-first default threshold `0.8`; `--balanced-thresholds` uses `0.5`.
   - Unknown/Neutral/Transitional labels are forced to `decision=abstain`.
   - Report includes per-label precision/recall/F1/Brier proxy/ECE proxy/support/threshold plus `purged_split_interface` with `embargo_bars`.

5. R6 conformal calibration
   - `scripts/research/regime_conformal_calibration_report.py`
   - `scripts/research/tests/test_regime_conformal_calibration_report.py`
   - Reads R5 scores plus training report.
   - Optional `--truth` labels keyed by `timestamp`; missing truth does not fail.
   - Emits `regime_conformal_calibration_report.json`.
   - Defaults target coverages `[0.95, 0.99]`; repeated `--target-coverage` can override.
   - Hot-plug consumer scope via `--label-prefix` (e.g. `primary::`, `volatility::`, `primary::Trend`).
   - Emits singleton rate, max/average conformal set size, class-conditional coverage, `confidence_95`, `confidence_99`.
   - Unknown/Neutral/Transitional labels remain `trade_usable=false`.

6. R7 distributional agreement
   - `scripts/research/regime_distributional_agreement_report.py`
   - `scripts/research/tests/test_regime_distributional_agreement_report.py`
   - Reads R3 features, R5 scores, and R6 conformal report.
   - Emits `regime_distributional_agreement_report.json`.
   - Pure-Python quantile/energy-distance proxy fallback; no scipy dependency.
   - Compares current feature window to built-in ICT primary label archetypes.
   - Supports `--label-prefix` hot-plug consumer scope and `--window` current-feature window.
   - Emits `top_label`, `nearest_archetype_label`, `label_distances`, `agreement`, `transitional_flag`, and `transitional_reasons`.
   - Keeps user VRP/NQ fields visible under `feature_group_summaries.user_vrp_nq`: `qqq_hv_level`, `nq_vs_200d_pct`, `vix3m_level`, `qqq_hv_pct_rank_252`, `vvix_over_vix`.

7. R8 transition governor
   - `scripts/research/regime_transition_governor.py`
   - `scripts/research/tests/test_regime_transition_governor.py`
   - Reads R5 scores, R6 conformal report, and R7 distributional report.
   - Optional `--hmm-report` and `--drift-rows`; missing optional files must not fail.
   - Emits `regime_transition_governor_report.json`.
   - Pure-Python hysteresis and transition guardrail fallback; no dependency.
   - Supports `--label-prefix` hot-plug consumer scope and `--min-duration` hysteresis.
   - Emits `transition_hazard`, `guardrail_reasons`, `execution_tree_hint` (`accept_regime` / `transition_guardrail` / `unknown_abstain`), and `bbn_evidence_hint`.
   - Wide conformal sets, unknown labels, failed confidence, distributional disagreement, transitional flags, short duration, flip-flops, HMM low persistence, and external drift flags become guardrail reasons.

8. R9 high-confidence decision aggregator
   - `scripts/research/regime_high_confidence_decision.py`
   - `scripts/research/tests/test_regime_high_confidence_decision.py`
   - Reads R5 scores, R6 conformal report, R7 distributional report, and R8 transition governor report.
   - Emits `regime_high_confidence_decision.json`.
   - Pure-Python final consumer decision fallback; no dependency.
   - Supports `--label-prefix` hot-plug consumer scope.
   - Emits decision states: `single_label_95`, `single_label_99`, `label_set`, `transitional`, `unknown_abstain`.
   - Emits `trade_usable`, `final_label`, `label_set`, compact `abstain_reasons`, `execution_tree_hint`, `bbn_evidence_hint`, `path_ranker_context`, and `user_vrp_nq_context`.
   - Keeps main runtime unchanged; user opts in by invoking the sidecar.

9. R10 consumer bundle / manifest
   - `scripts/research/regime_consumer_bundle.py`
   - `scripts/research/tests/test_regime_consumer_bundle.py`
   - Reads any subset of R2-R9 artifacts via repeated `--include-artifact key=path`.
   - Optional `--artifact-dir` auto-discovers default artifact names.
   - Emits compact `regime_consumer_bundle.json` with `latest_decision`, `consumer_hints`, artifact paths/schema versions, and `missing_artifacts`.
   - Missing artifacts are reported, not fatal.
   - Pure-Python token-friendly manifest fallback; no dependency and no runtime mutation.

10. R11 sidecar pipeline runner
   - `scripts/research/regime_sidecar_pipeline.py`
   - `scripts/research/tests/test_regime_sidecar_pipeline.py`
   - User doc: `docs/regime-classifier-sidecar-chain.md`.
   - One command runs R2-R10 when `--ohlcv` is provided.
   - Supports `--output-dir`, `--label-prefix`, `--auxiliary-evidence`, and `--truth`.
   - Missing `--ohlcv` prints an input contract, exits `2`, and does not create repo-root state.
   - Emits compact final decision and bundle path; no runtime mutation.

11. R12 mainline adapter spec
   - `docs/regime-consumer-bundle-mainline-adapter-spec.md`
   - `docs/plans/2026-05-09-regime-classifier-r12-handoff-todo.md`
   - Spec-only slice; no Rust implementation.
   - Defines optional `--regime-consumer-bundle <PATH>`, `--regime-consumer-bundle-strict`, config key `regime_consumer_bundle.{path,strict,enabled}`, consumer mapping table, no-op/default behavior, strict/non-strict behavior, and no-pollution rules.

12. R13 optional Rust adapter stub
   - `src/application/regime/consumer_bundle_adapter.rs`
   - `tests/regime_consumer_bundle_adapter.rs`
   - `docs/plans/2026-05-09-regime-classifier-r13-handoff-todo.md`
   - Adds `RegimeConsumerBundleAdapter::load_optional(path, strict)` with disabled/no-op default.
   - Non-strict missing/invalid bundle returns neutral adapter; strict missing/invalid returns error.
   - Reads only explicit bundle path, maps known fields, does not wire into mainline commands, and never executes Python sidecars.

13. R14 adapter read-only trace surface
   - `src/application/regime/consumer_bundle_adapter.rs`
   - `tests/regime_consumer_bundle_adapter.rs`
   - `docs/plans/2026-05-09-regime-classifier-r14-handoff-todo.md`
   - Adds `RegimeConsumerBundleAdapter::trace_entries(path)`.
   - Emits compact trace values: `regime_bundle_status`, `regime_bundle_path`, `regime_bundle_error`, `regime_decision_state`, `regime_trade_usable`, `regime_final_label`, and `regime_execution_tree_hint`.
   - Read-only and side-effect free; no mainline command behavior change.

14. R15 analyze trace-only wiring
   - `src/main.rs`
   - `src/analyze_command.rs`
   - `docs/plans/2026-05-09-regime-classifier-r15-handoff-todo.md`
   - Adds explicit `analyze` flags: `--regime-consumer-bundle <PATH>` and `--regime-consumer-bundle-strict`.
   - Loads the Rust adapter only when the flag is present and appends trace-only context to `supporting.artifact_action_summary`.
   - Adds joined `regime_bundle_trace:*` line so compact outputs retain full trace context.
   - Strict missing/invalid must be loaded before state/data mutation so failures are early.
   - Does not alter execution branch, BBN posterior, path-ranker rows, recommendation logic, or invoke Python sidecars.

15. R16 analyze-live trace-only wiring
   - `src/main.rs`
   - `src/analyze_live_command.rs`
   - `docs/plans/2026-05-09-regime-classifier-r16-handoff-todo.md`
   - Adds explicit `analyze-live` flags: `--regime-consumer-bundle <PATH>` and `--regime-consumer-bundle-strict`.
   - Loads `RegimeConsumerBundleAdapter` before live provider/network work when the flag is present.
   - Appends read-only trace into `supporting.artifact_action_summary` and joined `regime_bundle_trace:*` line.
   - Strict missing/invalid exits before live fetches.
   - Does not mutate execution branch, BBN posterior, path-ranker rows, recommendation logic, or invoke Python sidecars.

16. R17 read-only BBN soft-evidence mapper
   - `src/application/regime/consumer_bundle_adapter.rs`
   - `tests/regime_consumer_bundle_adapter.rs`
   - `docs/plans/2026-05-09-regime-classifier-r17-handoff-todo.md`
   - Adds `RegimeBbnEvidenceStrength` and `RegimeReadOnlyBbnSoftEvidence`.
   - Adds `RegimeConsumerBundleAdapter::to_read_only_bbn_soft_evidence()`.
   - Mapping: `single_label_99 + trade_usable=true` -> `Strong` weight `0.9`; `single_label_95 + trade_usable=true` -> `Moderate` weight `0.65`; `label_set` / `transitional` / `unknown_abstain` / missing / invalid -> `Neutral` weight `0.0`.
   - Read-only only: do not call `EvidenceManager::insert_soft` or mutate BBN posterior until a later explicit opt-in slice.

## Verification Commands

```bash
python3 -m unittest scripts/research/tests/test_regime_ontology_manifest.py -v
python3 -m unittest scripts/research/tests/test_regime_feature_builder.py -v
python3 -m unittest scripts/research/tests/test_regime_discovery.py -v
python3 -m unittest scripts/research/tests/test_regime_expert_trainer.py -v
python3 -m unittest scripts/research/tests/test_regime_conformal_calibration_report.py -v
python3 -m unittest scripts/research/tests/test_regime_distributional_agreement_report.py -v
python3 -m unittest scripts/research/tests/test_regime_transition_governor.py -v
python3 -m unittest scripts/research/tests/test_regime_high_confidence_decision.py -v
python3 -m unittest scripts/research/tests/test_regime_consumer_bundle.py -v
python3 -m unittest scripts/research/tests/test_regime_sidecar_pipeline.py -v
cargo test --test regime_consumer_bundle_adapter
cargo check
python3 -m unittest discover -s scripts/research/tests -p 'test_*.py'
```

Observed final sweep after R17: `cargo test --test regime_consumer_bundle_adapter` -> 11 passed; `cargo check` -> OK. R17 RED was verified first by running the new strong-evidence test and seeing unresolved import / missing method errors. R16/R15 CLI smokes confirmed compact analyze/analyze-live output contains `regime_bundle_status=loaded`, `regime_decision_state=single_label_99`, and `regime_execution_tree_hint=accept_regime`; strict missing-bundle smokes exit nonzero with `missing`. Last full Python sidecar sweep after R11: 91 tests OK.

## CLI Smoke Pattern

Use `/tmp` or explicit output dirs; do not write repo-root state. Minimal consumer smoke:

```bash
python3 scripts/research/regime_ontology_manifest.py \
  --output-json /tmp/ict-regime/regime_ontology_manifest.json \
  --output-jsonl /tmp/ict-regime/regime_expert_bank_manifest.jsonl
python3 scripts/research/regime_feature_builder.py \
  --ohlcv /tmp/ict-regime/ohlcv.csv \
  --output-features /tmp/ict-regime/regime_features.csv \
  --output-report /tmp/ict-regime/feature_quality_report.json
python3 scripts/research/regime_expert_trainer.py \
  --ontology /tmp/ict-regime/regime_ontology_manifest.json \
  --features /tmp/ict-regime/regime_features.csv \
  --output-scores /tmp/ict-regime/regime_expert_scores.jsonl \
  --output-report /tmp/ict-regime/regime_expert_training_report.json
python3 scripts/research/regime_conformal_calibration_report.py \
  --scores /tmp/ict-regime/regime_expert_scores.jsonl \
  --training-report /tmp/ict-regime/regime_expert_training_report.json \
  --truth /tmp/ict-regime/regime_truth.jsonl \
  --label-prefix primary:: \
  --output-json /tmp/ict-regime/regime_conformal_calibration_report.json
python3 scripts/research/regime_distributional_agreement_report.py \
  --features /tmp/ict-regime/regime_features.csv \
  --scores /tmp/ict-regime/regime_expert_scores.jsonl \
  --conformal-report /tmp/ict-regime/regime_conformal_calibration_report.json \
  --label-prefix primary:: \
  --output-json /tmp/ict-regime/regime_distributional_agreement_report.json
python3 scripts/research/regime_transition_governor.py \
  --scores /tmp/ict-regime/regime_expert_scores.jsonl \
  --conformal-report /tmp/ict-regime/regime_conformal_calibration_report.json \
  --distributional-report /tmp/ict-regime/regime_distributional_agreement_report.json \
  --label-prefix primary:: \
  --min-duration 3 \
  --output-json /tmp/ict-regime/regime_transition_governor_report.json
python3 scripts/research/regime_high_confidence_decision.py \
  --scores /tmp/ict-regime/regime_expert_scores.jsonl \
  --conformal-report /tmp/ict-regime/regime_conformal_calibration_report.json \
  --distributional-report /tmp/ict-regime/regime_distributional_agreement_report.json \
  --governor-report /tmp/ict-regime/regime_transition_governor_report.json \
  --label-prefix primary:: \
  --output-json /tmp/ict-regime/regime_high_confidence_decision.json
python3 scripts/research/regime_sidecar_pipeline.py \
  --ohlcv /tmp/ict-regime/ohlcv.csv \
  --auxiliary-evidence /tmp/ict-regime/aux.csv \
  --truth /tmp/ict-regime/regime_truth.jsonl \
  --output-dir /tmp/ict-regime \
  --label-prefix primary::Trend
```

Expected one-command R11 smoke: prints `status=ok`, `bundle_path`, and `final_decision`; clean narrowed-scope smoke can produce `decision_state=single_label_99`, `trade_usable=true`, `final_label=primary::TrendExpansion`. Missing `--ohlcv` exits `2`, prints `input_contract.required=["--ohlcv"]`, and does not create repo-root state.

Expected R5 full-ontology smoke: `expert_count=53`, score rows equal `feature_rows * 53`, `mode=pure_python_threshold_fallback`, `ontology_mutation=read_only`.

Expected R6 smoke: report is written even if confidence gates fail; failure is valid evidence. With full primary scope, broad sets may produce `confidence_95=false`, `confidence_99=false`, `singleton_rate<1`. Consumers can narrow scope with `--label-prefix`.

Expected R7 smoke: report is written with `top_label`, `nearest_archetype_label`, `agreement`, and `transitional_flag`; `agreement=disagree` or `transitional_flag=true` is valid evidence rather than command failure. If auxiliary evidence is present, `feature_group_summaries.user_vrp_nq` should include `qqq_hv_level`, `nq_vs_200d_pct`, `vix3m_level`, `qqq_hv_pct_rank_252`, and `vvix_over_vix`.

Expected R8 smoke: report is written with `current_label`, `transition_hazard`, `guardrail_reasons`, `execution_tree_hint`, and `bbn_evidence_hint`. A clean stable run can produce `execution_tree_hint=accept_regime`, `transition_hazard=0.0`, `guardrail_reasons=[]`. Flip-flops, short duration, failed confidence, wide conformal sets, distributional disagreement, unknown labels, low HMM persistence, or drift flags should produce guardrail/abstain rather than command failure.

Expected R9 smoke: report is written with `decision_state`, `trade_usable`, `final_label`, `label_set`, `execution_tree_hint`, `bbn_evidence_hint`, `path_ranker_context`, and `user_vrp_nq_context`. Clean narrowed-scope smoke can produce `decision_state=single_label_99`, `trade_usable=true`, `final_label=primary::TrendExpansion`, `execution_tree_hint=accept_regime`, `abstain_reasons=[]`. Broad/noisy scope may produce `label_set`, `transitional`, or `unknown_abstain`; treat this as consumer-safe evidence, not script failure.

Expected R10 smoke: bundle is written with `latest_decision`, `consumer_hints`, `artifacts`, `missing_artifacts`, and `consumer_contract`. Clean R2-R9 artifact dir can produce `artifact_count=7`, `missing_artifacts=[]`, `decision_state=single_label_99`, `trade_usable=true`, `execution_tree_hint=accept_regime`, and a small (<7KB) JSON bundle. Missing optional artifacts should appear under `missing_artifacts` and should not fail the script.

## Handoff Convention

Write live board docs in `docs/plans/*-handoff-todo.md` with:
- Done
- Verification
- CLI Floor
- Consumer Contract
- Immediate Next Slice
- Commit Plan
- Worktree exclusions

For this chain, handoff files:
- `docs/plans/2026-05-09-regime-classifier-r2-r4-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r5-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r6-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r7-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r8-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r9-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r10-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r11-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r12-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r13-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r14-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r15-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r16-handoff-todo.md`
- `docs/plans/2026-05-09-regime-classifier-r17-handoff-todo.md`

## Pitfalls

- TDD RED summaries can confuse the user if phrased as current failure. Say `RED verified: missing module before implementation; GREEN now passes`.
- Keep ontology read-only in discovery/training/calibration steps; sidecars may propose or score labels but must not mutate the fixed ontology.
- R5/R6 should be consumer-usable without optional dependencies: prefer deterministic fallbacks before adding ML packages.
- Treat optional R4 reports and R6 truth labels as advisory inputs; missing optional files must not block the sidecar.
- Unknown/Neutral/Transitional labels must remain abstain/non-trade-usable even if numerical score crosses a threshold.
- R6 confidence gates can legitimately fail on broad label scopes; do not treat `confidence_95=false` as command failure. It means the current score set is not singleton/high-coverage enough.
- R7 `agreement=disagree` or `transitional_flag=true` can be correct output, not failure; it means the distributional archetype check is warning that score-top, conformal set, and feature geometry are not aligned.
- R8 `execution_tree_hint=transition_guardrail` / `unknown_abstain` is often the desired safe output, not a failed command. Treat it as a machine-readable decision unless the script exits nonzero or required fields are missing.
- R8 smoke with broad `primary::` scope may guardrail because conformal/distributional gates are noisy; use narrower `--label-prefix primary::Trend` for a clean stable-path acceptance smoke, but keep broad-scope guardrail tests too.
- Add hot-plug scope knobs (`--label-prefix`, profile/config files) when broad expert banks make consumer output noisy.
- Commit only the sidecar chain; run `git diff --cached --name-only` before commit and exclude unrelated Rust dirty files or unrelated handoff docs.
- Watch for unexpected commits by other agents while working. If a commit appears containing unrelated files, do not amend or revert it unless asked; create a clean follow-up commit with only your staged files.
- Use the actual available edit tool. If shell `apply_patch` is missing, use the Hermes patch tool rather than switching to `cat`/Python writes.
- Verify new files exist and tests pass after creation.
