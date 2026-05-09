# 2026-05-09 VRP V2 Loop Handoff TODO

> Live handoff for the loop that explicitly pushed one candidate through factor artifact -> pre-bayes -> BBN -> CatBoost/path-ranking -> execution-tree. Keep this doc command/evidence focused and `/tmp/...` isolated.

## Scope

- Candidate: `VRPCompression_V2_NQ_15m`
- State dir: `/tmp/vrp-v2-loop-20260509`
- Candidate pack: `/tmp/vrp-v2-loop-20260509-candidate-pack/`
- Manifest: `/tmp/vrp_v2_strategy_library.json`
- Realized trades: `/tmp/vrp_v2_realized_trades.jsonl`
- Candidate spec: `/tmp/vrp-v2-loop-20260509-candidate-spec.json`
- Runtime boundary: no `ict-engine` runtime source changes for this slice.
- Repo pollution boundary: generated data stays under `/tmp`; this doc records paths and results only.

## Done

- [x] Created explicit candidate spec with downstream targets:
  - `pre_bayes_targets`
  - `belief_targets`
  - `path_ranking_targets`
  - `execution_tree_targets`
  - `structural_feedback_required=true`
- [x] Generated candidate pack with:
  - `/tmp/vrp-v2-loop-20260509-candidate-pack/factor_expression.json`
  - `/tmp/vrp-v2-loop-20260509-candidate-pack/factor_eval_grid_summary.json`
  - `/tmp/vrp-v2-loop-20260509-candidate-pack/transfer_score.json`
- [x] Ran pre-bayes status from the same isolated state:
  - command: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine pre-bayes-status --symbol NQ --state-dir /tmp/vrp-v2-loop-20260509 --human`
  - result: `gate=pass_neutralized`, `soft_evidence=yes`
  - bridge: `long=0.551`, `short=0.530`, `mtf=bullish`, `align=1.000`, `entry_align=0.860`
- [x] Ran BBN prior-init dry-run:
  - command: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine auto-quant-prior-init --symbol NQ --state-dir /tmp/vrp-v2-loop-20260509 --library /tmp/vrp_v2_strategy_library.json --dry-run`
  - strategy: `VRPCompression_V2_NQ_15m`
  - trades: `815` (`n_win=277`, `n_loss=538`, `n_breakeven=0`)
  - prior moved from `[0.34275405214176413, 0.001986731343802505, 0.6552592165144334]` to `[0.33990526417634764, 0.00001931209082675582, 0.6600754237328257]`
- [x] Checked realized-trade ingestion dry-run:
  - command: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine auto-quant-ingest-real-trades --symbol NQ --state-dir /tmp/vrp-v2-loop-20260509 --trades /tmp/vrp_v2_realized_trades.jsonl --dry-run`
  - result: refused duplicate content hash `fc131fe2cce235f5`
  - interpretation: feedback already exists in the copied state; do not force-reingest without rolling back BBN state.
- [x] Exported structural path-ranking target:
  - command: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine export-structural-path-ranking-target --symbol NQ --state-dir /tmp/vrp-v2-loop-20260509`
  - rows: `3`
  - mature_rows: `0`
  - rows_with_raw_path_score: `3`
  - rows_with_calibrated_path_prob: `0`
  - rows_with_propensity_estimate: `1`
  - output CSV: `/tmp/vrp-v2-loop-20260509/NQ/policy_training/structural_path_ranking_target.csv`
- [x] Checked CatBoost/path-ranking status:
  - command: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine policy-training-status --symbol NQ --state-dir /tmp/vrp-v2-loop-20260509 --human`
  - result: `trainer_artifact=ready`, `trainer_status=present_validation_insufficient`, `runtime_selection=enabled_candidate_set_ready`, `runtime_mode=candidate_set_only`, `runtime_source=candidate_set`, `runtime_matches=3`
  - blocker: `mature_rows=0`, `raw_scored_mature=0/30`, `production_validation=0/30`, `calibration=not_fitted`
- [x] Checked execution-tree/workflow status:
  - command: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine workflow-status --symbol NQ --state-dir /tmp/vrp-v2-loop-20260509 --human`
  - result: `analyze | pass_neutralized`, `quality=0.607`
  - ranker: `status=using_candidate_set_scores`, `source=candidate_set`, `applied=3`, `artifact=0`, `candidate=3`, `raw=0.470`
- [x] Checked workflow phases:
  - `ensemble-vote`: `action=Observe`, `confidence=0.464`, `comparable=no_previous_run`
  - `structural-playbook`: selected branch `trend_follow_through`, posterior about `0.464`, candidate-set path ranking active
  - `structural-recommended-path-bundle`: `trend_follow_through`, `posterior=0.464`, `selected_prob=0.370`

## Chain Verdict

- Verdict: `stopped_at_path_ranking`
- Factor stage: candidate has explicit pack and dense NQ evidence (`815` trades) plus cross-market evidence recorded in candidate spec.
- Pre-bayes stage: alive and pass-neutralized, not blocking.
- BBN stage: prior-init alive; realized-trade feedback already present in copied state.
- CatBoost/path-ranking stage: current blocker. The runtime can use candidate-set scores, but mature external ranker closure is not validated because `mature_rows=0`, `raw_scored_mature=0/30`, and `production_validation=0/30`.
- Execution-tree stage: alive and readable, but still observes via candidate-set ranker rather than a mature external CatBoost loop.

## Next

- [ ] Do not force-reingest `/tmp/vrp_v2_realized_trades.jsonl` into the copied state unless intentionally rolling back BBN feedback first.
- [ ] Use the generated structural target CSV to produce a hot-plug external CatBoost/direct ranker artifact, then re-run `policy-training-status` to see whether runtime selection moves beyond `candidate_set_only`.
- [ ] Keep the ranker artifact optional/hot-pluggable: consumer can use candidate-set scoring with zero config, or opt into the external ranker when enough validation rows exist.
- [ ] If mature rows remain zero, the next practical slice should generate or import structural feedback rows rather than tuning the trainer again.
- [ ] Keep all generated ranker experiments under `/tmp/...` or explicit caller-owned state dirs; do not write model artifacts to repo root.

## Drift Check

- Scope: still serving the original loop request: factor -> pre-bayes/filter -> BBN -> CatBoost/path-ranking -> execution tree.
- Compatibility: zero-config remains intact; no runtime source edit was made for this handoff.
- Pollution: generated artifacts are `/tmp` only; repo receives this handoff doc.
- Decision: continue with path-ranking maturity / hot-plug ranker validation next.
