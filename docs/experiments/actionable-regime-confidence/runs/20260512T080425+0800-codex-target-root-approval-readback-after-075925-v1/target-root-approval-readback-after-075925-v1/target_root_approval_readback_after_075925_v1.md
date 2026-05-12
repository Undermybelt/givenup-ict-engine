# Target Root Approval Readback After 075925 v1

Run id: `20260512T080425+0800-codex-target-root-approval-readback-after-075925-v1`

Gate result: `target_root_approval_readback_after_075925_v1=no_target_root_or_approval_unlock`

## Scope

Read-only exact target-root and approval-package readback after the settled `075925` public dataset-hub probe. This checks only the Board A roots that would allow direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree promotion to proceed. It does not mutate target roots, approve controls, derive labels, run downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- R6 owner/export root complete: `False`.
- R5 recency root complete: `False`.
- R3 native-subhour root complete: `True`.
- R3 Crisis supported: `False`.
- Direct manipulation intake present: `True`.
- Direct manipulation intake is owner/export root: `False`.
- Approval package exists: `True`.
- Approval present: `False`.
- Canonical merge allowed now: `False`.
- Downstream rerun allowed now: `False`.

## Decision

No exact target root or approval state currently unlocks Board A promotion. `/tmp/ict-engine-board-a-r6-owner-export-v1` and `/tmp/ict-engine-source-panel-recency-extension` are absent; `/tmp/ict-engine-native-subhour-source-label-intake` is present but still Crisis-incomplete; `/tmp/ict-engine-direct-manipulation-row-intake` is present but is not the R6 owner/export root and does not override the explicit approval package, where `approval_present=false`, `canonical_merge_allowed_now=false`, and `downstream_rerun_allowed_now=false`.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T080425+0800-codex-target-root-approval-readback-after-075925-v1/target-root-approval-readback-after-075925-v1/target_root_approval_readback_after_075925_v1.json`
- Required-file CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T080425+0800-codex-target-root-approval-readback-after-075925-v1/target-root-approval-readback-after-075925-v1/target_root_required_files_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T080425+0800-codex-target-root-approval-readback-after-075925-v1/checks/target_root_approval_readback_after_075925_v1_assertions.out`

## Next

Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until an exact required root or explicit approval unlock appears.
