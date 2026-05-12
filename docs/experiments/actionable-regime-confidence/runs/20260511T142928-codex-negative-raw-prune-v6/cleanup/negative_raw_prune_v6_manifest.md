# Negative Raw Prune v6

Run id: `20260511T142928+0800-codex-negative-raw-prune-v6`

Scope: prune repo-local heavy raw/intermediate artifacts from blocked or negative Board A loops after compact reports/checks already captured the decision. This cleanup does not edit Current Cursor, gates, thresholds, runtime code, or next action.

## Pre-Cleanup Readback

- Board file: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`
- Current cursor observed: `20260511T140643+0800-codex-amd-cvx-exact-intraday-source-attachment-v1`, then another agent advanced the board to `exact_1h_source_universe_expansion_v1` while this cleanup was running.
- Runs dir pre-cleanup size: `116M`

## Deleted Artifacts

| Path | Bytes | Reason | Retained Evidence |
|---|---:|---|---|
| `docs/experiments/actionable-regime-confidence/runs/20260511T001100-sector-index-breadth-root-probe/provider/` | `10129354` | blocked sector/index breadth root probe accepted no roots; provider OHLCV rows are raw reproduction input, not accepted evidence | `sector_index_breadth_root_report.json`, `sector_index_breadth_root_summary.csv`, assertions |
| `docs/experiments/actionable-regime-confidence/runs/20260511T031605-codex-persistent-hmm-root-posterior-gate/persistent-hmm-root-posterior-gate/persistent_hmm_root_scores.csv` | `9500022` | blocked HMM posterior gate added no new roots; full per-row score matrix is intermediate, while summary/sample/report/checks preserve the negative decision | `persistent_hmm_root_gate_report.json`, `persistent_hmm_root_gate_report.md`, `persistent_hmm_root_gate_summary.csv`, `persistent_hmm_root_score_sample.csv`, assertions |

## Result

- Deleted paths: `2`
- Deleted bytes: `19629376`
- Expected repo `runs/` size after cleanup: about `97M`
- Full objective achieved: `false`
- Thresholds relaxed: `false`
- Runtime code changed: `false`
- Raw provider bars retained for these negative slices: `false`

## Guardrail

For negative/blocked loops, keep provider downloads, replay-sized matrices, full row-score tables, and copied runtime state under `/tmp` or `/private/tmp`. Repo run roots should keep compact JSON/MD/check/script/sample artifacts unless the active board explicitly names a heavy file as current evidence.
