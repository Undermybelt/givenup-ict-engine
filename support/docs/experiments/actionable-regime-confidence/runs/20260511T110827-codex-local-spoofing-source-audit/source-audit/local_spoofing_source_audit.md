# Local Spoofing Source Audit

Run ID: `20260511T110827+0800-codex-local-spoofing-source-audit`

## Scope

- Active taxonomy: `MainRegimeV2`.
- Target lane: `Manipulation` direct spoofing/layering variety coverage.
- Acceptance requires timestamped positive/negative rows with order-lifecycle or L2/L3/MBO provenance.

## Candidate Decisions

| Candidate | Decision | Accepted Rows | Reason |
|---|---|---:|---|
| `navnoor_spoof_detection` | `rejected_code_not_replayable_direct_rows` | `0` | Local checkout contains model/notebook logic but no exported timestamped positive/negative spoofing rows or same-venue negative controls. |
| `quantsingularity_spoofing` | `rejected_synthetic_framework_no_real_labeled_rows` | `0` | Repository provides framework, adapters, expected data schema, and synthetic spoofing injection, but no replayable real timestamped positive/negative spoofing dataset in the local checkout. |

## Decision

- Accepted direct `Manipulation` rows added: `0`.
- Accepted direct variety coverage added: `0`.
- Accepted MainRegimeV2 parent-root slots added: `0`.
- Gate result: `blocked_local_spoofing_sources_no_replayable_positive_negative_rows`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
