# Partial Root Hygiene Readback After 0135 v1

- Gate result: `partial_root_hygiene_readback_after_0135_v1=partial_roots_not_evidence_r6_r3_r5_missing_no_promotion`.
- Reviewed only the newly visible partial roots after the latest 0130xx registrations.
- `20260512T013436-codex-provider-autoquant-readonly-refresh-after-0130-v1`: `partial_command_capture_only_not_evidence`; files `23`; reports `0`; JSON `0`; assertions `0`; board refs `0`.
- `20260512T013502-codex-readonly-runtime-surface-registration-after-0130xx-review-v1`: `absent_not_evidence`; files `0`; reports `0`; JSON `0`; assertions `0`; board refs `0`.
- Source-label equivalence root ready: `true`; R6 owner-export ready: `false`; R3 native-subhour ready: `false`; R5 recency ready: `false`.
- Accepted rows added: `0`; new confidence gate: false; canonical merge allowed: false; downstream chain rerun allowed: false.
- Runtime code changed: false. Shared intake mutated: false. R3/R5/R6 roots mutated: false. Thresholds relaxed: false. Raw data committed: false. External requests sent: false. Trade usable: false.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T013605-codex-partial-root-hygiene-readback-after-0135-v1/partial-root-hygiene-readback-after-0135-v1/partial_root_hygiene_readback_after_0135_v1.json`
- New-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T013605-codex-partial-root-hygiene-readback-after-0135-v1/partial-root-hygiene-readback-after-0135-v1/new_root_status_after_0135_v1.csv`
- Tmp-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T013605-codex-partial-root-hygiene-readback-after-0135-v1/partial-root-hygiene-readback-after-0135-v1/tmp_root_status_after_0135_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T013605-codex-partial-root-hygiene-readback-after-0135-v1/checks/partial_root_hygiene_readback_after_0135_v1_assertions.out`

Next:
- Preserve the Current Cursor next action for R6. Treat partial command captures and empty scaffolds as non-evidence until report, JSON, provenance, and assertions exist.
