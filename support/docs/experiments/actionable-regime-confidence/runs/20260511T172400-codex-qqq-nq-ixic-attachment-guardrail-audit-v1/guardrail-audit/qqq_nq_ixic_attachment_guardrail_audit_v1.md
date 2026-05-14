# QQQ/NQ IXIC Attachment Guardrail Audit v1

Run ID: `20260511T172400+0800-codex-qqq-nq-ixic-attachment-guardrail-audit-v1`

This is a guardrail audit for the `20260511T170714` QQQ/NQ daily cross-market attachment artifact. It does not delete or rewrite that artifact; it constrains how downstream agents may use it.

## Decision

`qqq_nq_ixic_attachment_guardrail_audit_v1=provenance_only_not_source_label_equivalence`

The `^IXIC -> QQQ/NQ=F` attachment may be used as:

- daily tracking diagnostics;
- target availability/readiness evidence;
- cross-market attachment provenance for a future owner-approved equivalence review.

It must not be used as:

- target-side `QQQ` or `NQ=F` source labels;
- `MainRegimeV2` confidence-gate rows for `QQQ` or `NQ=F`;
- full-market/full-species objective completion;
- a substitute for Nasdaq-100-grade source labels;
- a substitute for owner-approved `^IXIC -> QQQ/NQ/^NDX` equivalence policy.

## Evidence

- The earlier NDX source-label availability probe found no `^NDX`/`NDX` source labels and rejected `^IXIC` as a near-underlying proxy for `QQQ`, `^NDX`, or `NQ=F`.
- The `170714` artifact validates daily tracking correlation but does not provide source-owned Nasdaq-100 labels or an owner-approved equivalence policy.
- The `170714` assertion reports `target_root_cell_presence_wilson95_lcb=0.675592435116`, so it is not a 95 confidence source-label gate.
- The source-label equivalence request requires source-native labels or explicit owner approval before QQQ/NQ can count as target-side source labels.

## Result

- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full objective achieved: `false`.
- `update_goal`: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

## Next

Acquire actual Nasdaq-100-grade source labels or an owner-approved `^IXIC -> QQQ/NQ/^NDX` equivalence policy before using `QQQ`/`NQ=F` as source-label targets.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T172400-codex-qqq-nq-ixic-attachment-guardrail-audit-v1/guardrail-audit/qqq_nq_ixic_attachment_guardrail_audit_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T172400-codex-qqq-nq-ixic-attachment-guardrail-audit-v1/checks/qqq_nq_ixic_attachment_guardrail_audit_v1_assertions.out`
