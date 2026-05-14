# Recent Source Probe Rollup

Run ID: `20260511T090639+0800-codex-recent-source-probe-rollup`

Board: Board A, `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Result

- Active taxonomy: `MainRegimeV2`.
- Main price roots: `Bull`, `Bear`, `Sideways`, `Crisis`.
- Separate direct-event/order-lifecycle class or overlay: `Manipulation`.
- Accepted new MainRegimeV2 root-label slots: `0`.
- Accepted new direct `Manipulation` label sources: `0`.
- Accepted gate remains `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Gate result: `blocked_recent_source_probes_no_new_labels`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Consumed Runs

| Run | Decision | Accepted slots/sources | Reason |
|---|---|---:|---|
| `20260511T085230+0800-codex-nonkaggle-github-source-label-search` | `blocked_nonkaggle_github_search_no_attachable_root_label_panel` | `0` | GitHub metadata search found methodology/proxy repositories, not exact-underlying independent root-label panels. |
| `20260511T085653+0800-codex-zenodo-direct-manipulation-candidate-probe` | `blocked_zenodo_candidates_false_positive_or_no_rows` | `0` | Six Zenodo candidates were non-financial, policy text, catalog, or unrelated spoofing/deepfake records; no financial manipulation positive/negative rows were materialized. |
| `20260511T085659+0800-codex-local-pine-regime-detector-audit` | `blocked_local_pine_indicator_is_proxy_logic_not_source_labels` | `0` | Local Pine indicator emits OHLCV-derived regime names, not source labels or direct manipulation event windows. |

## Next Action

Search outside the already-failed GitHub metadata, Zenodo false positives, and local Pine proxy lanes for exact-underlying non-Kaggle root-label panels or authenticated direct `Manipulation` rows.
