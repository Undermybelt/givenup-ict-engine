# Local Required Source/Control Sweep v1

Run id: `20260512T073629+0800-codex-local-required-source-control-sweep-v1`

Gate result: `local_required_source_control_sweep_v1=no_new_required_source_control_unlock`

## Scope

This packet is a bounded local filesystem and known target-root sweep. It inspects existing local artifacts only. It does not mutate R3/R5/R6 target roots, does not approve the R6 decision package, does not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- R6 owner/export root `/tmp/ict-engine-board-a-r6-owner-export-v1`: absent.
- R5 recency root `/tmp/ict-engine-source-panel-recency-extension`: absent.
- R3 native-subhour root exists, but its provenance is `sujinwo/tsie-market-regime-dataset` and its limitations include `Crisis has no direct TSIE source taxonomy class`; it remains non-promoting.
- Source-label equivalence root exists with `248440` rows, but its limitations say schema readiness is not Board A confidence acceptance and source confidence calibration remains fail-closed.
- R6 approval decision package exists at `/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid`, but `approval_present=False`, `canonical_merge_allowed_now=False`, and `downstream_rerun_allowed_now=False`.
- Candidate filename/path hits found locally: `119`. They are inventory/discoverability hits only, not accepted source/control roots.

## Decision

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; direct verifier run false; split calibration run false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T073629+0800-codex-local-required-source-control-sweep-v1/local-required-source-control-sweep-v1/local_required_source_control_sweep_v1.json`
- Target-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T073629+0800-codex-local-required-source-control-sweep-v1/local-required-source-control-sweep-v1/target_root_status_v1.csv`
- Candidate-hit CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T073629+0800-codex-local-required-source-control-sweep-v1/local-required-source-control-sweep-v1/candidate_file_hits_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T073629+0800-codex-local-required-source-control-sweep-v1/checks/local_required_source_control_sweep_v1_assertions.out`

## Next

Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.
