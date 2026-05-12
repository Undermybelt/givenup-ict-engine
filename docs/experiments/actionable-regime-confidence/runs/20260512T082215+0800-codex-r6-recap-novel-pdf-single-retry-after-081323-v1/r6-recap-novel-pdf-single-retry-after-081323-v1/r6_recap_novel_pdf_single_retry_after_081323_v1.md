# R6 RECAP Novel PDF Single Retry After 081323 v1

Run id: `20260512T082215+0800-codex-r6-recap-novel-pdf-single-retry-after-081323-v1`

Gate result: `r6_recap_novel_pdf_single_retry_after_081323_v1=rate_limited_no_body_no_control_unlock`

## Scope

Read-only classification of the existing retry command output for
`gov.uscourts.ilnd.316889.1.0.pdf`. This run does not issue a new network
request, does not download or parse a PDF, does not mutate any target intake
root, does not approve RECAP/PACER provenance or `FLIP` rows as controls, and
does not run verifier, canonical merge, AutoQuant, Pre-Bayes, BBN,
CatBoost/path-ranking, execution-tree promotion, or `update_goal`.

## Readback

- HTTP status: `429`
- Content type: `text/html`
- Body bytes: `964`
- Body is PDF: `false`
- Body is HTML: `true`
- CloudFront/CourtListener rate-limited: `true`
- PDF acquired: `false`
- Source-owned normal-control document: `false`

## Decision

The retry did not acquire a PDF. The stored body is an HTTP `429` HTML
rate-limit response from the CourtListener/CloudFront route, not a
verifier-native source document. Accepted rows added `0`; R6 owner/export
unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid
required-root unlock false; source/control evidence acquired false; canonical
merge false; selected-data AutoQuant promotion false; downstream promotion
rerun false; strict full objective false; trade usable false;
`promotion_allowed=false`; `update_goal=false`.

## Next

Continue source/control acquisition only. The live unblocker remains an
owner-approved/authenticated FINRA, venue-surveillance, CAT-like,
CME/Cboe/CFE/exchange order-lifecycle export with both positives and matched
normal controls, or explicit same-exhibit `FLIP`-as-control approval before any
verifier, split calibration, canonical merge, selected-data AutoQuant,
Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.
