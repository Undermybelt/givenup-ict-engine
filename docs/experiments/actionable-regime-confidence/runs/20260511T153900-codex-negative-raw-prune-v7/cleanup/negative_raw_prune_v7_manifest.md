# Negative Raw Prune v7

Run id: `20260511T153900+0800-codex-negative-raw-prune-v7`

Scope: prune repo-local raw/intermediate artifacts from blocked, negative, or context-only Board A loops after compact reports/checks already captured the decision. This cleanup does not edit Current Cursor, gates, thresholds, runtime code, or next action.

## Board Readback

- Board file: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`
- Initial cleanup readback observed cursor: `20260511T151720+0800-codex-spoofing-layering-matched-row-readiness-v1`.
- Before writing this manifest, another agent had advanced the board cursor to `20260511T153637+0800-codex-regime-factor-consumer-map-v1`; this cleanup preserved that cursor and did not rewrite it.
- Runs dir pre-cleanup size: `98M`.

## Deleted Artifacts

| Path | Bytes | Reason | Retained Evidence |
|---|---:|---|---|
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/ict-engine/state-copy/` | `6610944` | negative candidate search accepted additional subtype packets `0`; copied runtime state is intermediate and not needed after compact report/checks | `evidence_packet_per_regime_candidate_search.json`, `calibration/per_regime_candidate_search_report.json`, assertions |
| `docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/state-copy/` | `6610944` | context-only full-chain readback kept execution promotion blocked; copied runtime state is intermediate | `evidence_packet_full_chain_reaudit_fresh_loop.json`, README, provider/readback outputs |
| `docs/experiments/actionable-regime-confidence/runs/20260511T031936-codex-cftc-dealer-root-gate/cftc-dealer-gate/cftc_dealer_root_feature_table.csv` | `4497149` | blocked CFTC/dealer gate below 95 for Bull/Bear/Sideways; full feature matrix is intermediate | `cftc_dealer_root_gate_report.json`, `cftc_dealer_root_gate_report.md`, `cftc_dealer_root_gate_summary.csv`, `cftc_dealer_root_feature_sample.csv`, assertions |
| `docs/experiments/actionable-regime-confidence/runs/20260511T091716-local-filesystem-label-panel-audit/local-filesystem-audit/local_filesystem_label_panel_audit.json` | `1588874` | blocked local filesystem audit found no independent source-label panel; full scan detail is negative intermediate | `local_filesystem_label_panel_audit.md`, assertions, script |
| `docs/experiments/actionable-regime-confidence/runs/20260511T091716-local-filesystem-label-panel-audit/local-filesystem-audit/local_filesystem_label_panel_audit_candidates.csv` | `948318` | blocked local filesystem audit candidate list is negative scan detail | `local_filesystem_label_panel_audit.md`, assertions, script |
| `docs/experiments/actionable-regime-confidence/runs/20260511T020338-codex-fred-macro-root-evidence-probe/root-macro/fred_macro_root_feature_table_sample.csv` | `1246250` | blocked FRED macro sidecar accepted no new roots; large sample table is intermediate | `fred_macro_root_evidence_probe_report.json`, `fred_macro_root_evidence_probe_report.md`, `fred_macro_root_evidence_probe_summary.csv`, assertions |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/branch-chain/qqq-regime-branch-iteration/structural-replay-qqq-36/state/` | `4087808` | early Board A full-chain readback ended `abstain_no_calibrated_release_rule`; copied replay state is intermediate | `evidence_packet.json`, README, checks, compact readbacks |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/branch-chain/qqq-regime-branch-iteration/structural-replay-qqq-36/windows/` | `1032192` | early Board A full-chain readback kept no calibrated release rule; per-window replay files are intermediate | `evidence_packet.json`, README, checks, compact readbacks |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/branch-chain/qqq-regime-branch-iteration/candles/` | `1191936` | raw candle copies from early abstain loop; compact provider and evidence summaries remain | `evidence_packet.json`, README, checks, provider-agreement summaries |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/provider/` | `339968` | raw provider rows from early abstain loop; compact decision artifact remains | `evidence_packet.json`, README, checks |
| `docs/experiments/actionable-regime-confidence/runs/20260510T185125-board-b-handoff-codex/ict-engine/state/` | `3448832` | Board B handoff remained `trade_usable=false`; copied runtime state is intermediate | `evidence_packet_board_b_handoff.json`, README, direct ict-engine readbacks |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/execution-tree/entry_scan_512.tsv` | `253811` | early abstain loop had execution tree `0/512` pass/actionable; full scan table is intermediate | `evidence_packet.json`, `execution-tree/entry_scan_512_summary.json`, checks |

## Result

- Deleted paths: `12`.
- Deleted bytes: approximately `31857026`.
- Runs dir post-cleanup size: `67M`.
- Remaining repo-local files over `1M`: accepted/current positive artifacts and earlier accepted/full-chain state, not broad negative sweeps.
- Full objective achieved: `false`.
- Thresholds relaxed: `false`.
- Runtime code changed: `false`.
- Raw provider bars downloaded: `false`.

## Guardrail

For negative, blocked, superseded, or context-only loops, keep full row matrices, copied runtime state, replay logs, and provider downloads under `/tmp` or `/private/tmp`. Repo run roots should retain compact JSON/MD/check/script/sample artifacts unless the active board explicitly names a heavy file as current evidence.
