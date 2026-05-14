# Strict 1h Recency Tail Current Source Recheck v1

Run ID: `20260511T200909-codex-strict-1h-recency-tail-current-source-recheck-v1`

- Gate result: `strict_1h_recency_tail_current_source_recheck_v1=no_post_2026_01_30_source_owned_tail_rows`.
- Target: R5 strict `1h` recency-tail repair for XOM/Sideways, UNH/Bear, ^DJI/Sideways, and AMD/Bear.
- Local source panel exists: `True`; rows: `245021`; max date: `2026-01-30`.
- Rows after `2026-01-30` by strict target: XOM/Sideways=0, UNH/Bear=0, ^DJI/Sideways=0, AMD/Bear=0.
- Candidate source metadata checks: `10`; ready external tail sources: `0`.
- Kaggle current dataset metadata still points to the same public source panel; local row-level panel remains capped at `2026-01-30`.
- Hugging Face and GitHub metadata searches found no source-owned post-cutoff row package for the strict targets.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T200909-codex-strict-1h-recency-tail-current-source-recheck-v1/recency-tail-current-source-recheck/strict_1h_recency_tail_current_source_recheck_v1.json`
- Target CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T200909-codex-strict-1h-recency-tail-current-source-recheck-v1/recency-tail-current-source-recheck/strict_1h_recency_tail_current_source_recheck_v1_targets.csv`
- Candidate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T200909-codex-strict-1h-recency-tail-current-source-recheck-v1/recency-tail-current-source-recheck/strict_1h_recency_tail_current_source_recheck_v1_candidates.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T200909-codex-strict-1h-recency-tail-current-source-recheck-v1/checks/strict_1h_recency_tail_current_source_recheck_v1_assertions.out`
