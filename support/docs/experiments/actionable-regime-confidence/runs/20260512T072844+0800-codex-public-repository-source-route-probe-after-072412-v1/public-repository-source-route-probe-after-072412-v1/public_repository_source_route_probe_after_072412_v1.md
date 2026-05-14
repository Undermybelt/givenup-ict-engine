# Public Repository Source Route Probe After 072412 v1

## Decision

- Gate result: `exact_required_queries_no_promoting_hits_no_unlock`
- Accepted rows added: `0`
- Valid required-root unlock: `false`
- Source/control evidence acquired: `false`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- `update_goal`: `false`

## Public Surfaces Queried

- DataCite REST API
- OSF search API
- Figshare public articles search API
- Mendeley Data public web search page; unauthenticated Mendeley API access was not used for promotion

## Summary

- Queries: `13`
- Requests: `52`
- Failed/blocked requests: `0`
- Required filename hits: `0`
- Owner hits: `0`
- `MainRegimeV2` hits: `0`
- R3 native-subhour hits: `0`
- R5 recency hits: `0`
- Context-only order-book hits: `0`

## Non-Promotion Reason

The public searches did not supply verifier-native R6 owner/export positives, matched controls, provenance package, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, or verifier-native Crisis-capable R3 labels. Mendeley API access requires OAuth and was not used.

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.
