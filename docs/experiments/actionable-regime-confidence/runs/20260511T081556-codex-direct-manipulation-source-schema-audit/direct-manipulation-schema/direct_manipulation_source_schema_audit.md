# Direct Manipulation Source Schema Audit

Run id: `20260511T081556+0800-codex-direct-manipulation-source-schema-audit`

Goal achieved: `false`

## Summary

- Candidates schema-audited: `4`
- Direct input sources materialized: `2`
- Accepted direct `Manipulation` label sources: `0`
- MainRegimeV2 root-label slots added: `0`
- Manipulation label slots added: `0`
- Raw schema sample root: `/private/tmp/ict-regime-direct-manipulation-schema-20260511T081556`
- Raw schema samples committed: `false`

## Source Dispositions

| Source | Decision | Reason |
|---|---|---|
| trentmkelly/polymarket_crypto_derivatives | direct_input_source_unlabeled | direct order-book/order-lifecycle fields exist, but no explicit manipulation-positive/negative labels or event windows were found |
| phobia76/pmxt-l2-dump | direct_input_source_unlabeled | direct order-book/order-lifecycle fields exist, but no explicit manipulation-positive/negative labels or event windows were found |
| muhammetakkurt/pump-fun-meme-token-dataset | event_context_unlabeled | token/event context exists, but no explicit manipulation labels or order-lifecycle evidence were found |
| Washedashore/thepower | rejected_metadata_false_positive | dataset card is a generic template and does not provide market event/order-flow labels |

## Accounting

- Polymarket order-book / event schemas are useful direct-input provenance for a future `Manipulation` gate, but they are unlabeled.
- Pump.fun token/event context is not an accepted manipulation label panel because no explicit positive/negative manipulation windows were found.
- No audited source adds accepted `Bull` / `Bear` / `Sideways` / `Crisis` root labels.
- No threshold was relaxed and no runtime code was changed.

Gate result: `blocked_direct_manipulation_sources_unlabeled_no_accepted_label_windows`

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.
