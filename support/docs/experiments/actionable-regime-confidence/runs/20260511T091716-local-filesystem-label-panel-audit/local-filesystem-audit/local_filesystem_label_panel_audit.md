# Local Filesystem Label Panel Audit

Run ID: `20260511T091716+0800-local-filesystem-label-panel-audit`

## Result

- Search roots inspected: `4`.
- Files visited: `18105`.
- Candidate files classified: `2000`.
- Accepted independent MainRegimeV2 parent-root label sources: `0`.
- New attached parent-root slots: `0`.
- Accepted direct `Manipulation` label sources: `0`.
- Accepted direct `Manipulation` rows/windows: `0`.
- Gate result: `blocked_local_filesystem_no_new_independent_label_panel`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Decision Counts

`{'rejected_proxy_or_generated_label_file': 88, 'rejected_missing_full_mainregimev2_roots': 160, 'sidecar_direct_manipulation_candidate_needs_rows_and_controls': 288, 'rejected_no_exact_target_underlying': 4, 'partial_existing_kaggle_exact_panel_already_consumed': 2, 'rejected_repo_artifact_or_prior_probe': 1458}`

## Notes

- This audit used filenames and small headers/previews only; raw datasets were not copied into the repo.
- Repo-generated artifacts and already-counted Kaggle exact-label caches are provenance only, not new independent labels.
- Local HMM/HF/Pine/proxy files remain rejected unless a future source proves independent labels, exact targets, timeframes, and chronological windows.

## Next Action

Obtain an external exact-underlying parent-root label panel or authenticated direct `Manipulation` positive/negative rows; local caches inspected here do not add accepted slots.
