# Source Acquisition Request Draft Bundle v1

Run ID: `20260511T204729-codex-source-acquisition-request-draft-bundle-v1`

- Gate result: `source_acquisition_request_draft_bundle_v1=drafts_ready_not_sent_rows_not_acquired`.
- Source outbox: `source_acquisition_outbox_v1=outbox_ready_rows_not_acquired`.
- Drafts written: `5`.
- Requirements covered: `R2, R3, R4, R5, R6`.
- Request sent: `false`; rows acquired: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Boundary

This run only creates local no-send Markdown drafts from the existing source-acquisition outbox. It does not contact owners, use authenticated accounts, download private rows, create intake files, or promote proxy labels.

## Drafts

| Outbox ID | Requirements | Draft |
|---|---|---|
| `R2-source-label-equivalence-crossmarket` | `R2` | `docs/experiments/actionable-regime-confidence/runs/20260511T204729-codex-source-acquisition-request-draft-bundle-v1/source-acquisition-request-draft-bundle/drafts/r2-source-label-equivalence-crossmarket.md` |
| `R3-native-subhour-source-labels` | `R3` | `docs/experiments/actionable-regime-confidence/runs/20260511T204729-codex-source-acquisition-request-draft-bundle-v1/source-acquisition-request-draft-bundle/drafts/r3-native-subhour-source-labels.md` |
| `R4-R5-stock-regime-owner-recency-and-1h` | `R4;R5` | `docs/experiments/actionable-regime-confidence/runs/20260511T204729-codex-source-acquisition-request-draft-bundle-v1/source-acquisition-request-draft-bundle/drafts/r4-r5-stock-regime-owner-recency-and-1h.md` |
| `R6-do-putnins-spoofing-layering` | `R6` | `docs/experiments/actionable-regime-confidence/runs/20260511T204729-codex-source-acquisition-request-draft-bundle-v1/source-acquisition-request-draft-bundle/drafts/r6-do-putnins-spoofing-layering.md` |
| `R6-direct-manipulation-remaining-species` | `R6` | `docs/experiments/actionable-regime-confidence/runs/20260511T204729-codex-source-acquisition-request-draft-bundle-v1/source-acquisition-request-draft-bundle/drafts/r6-direct-manipulation-remaining-species.md` |

## Artifacts

- JSON: `source_acquisition_request_draft_bundle_v1.json`
- Draft index CSV: `source_acquisition_request_draft_bundle_v1.csv`
- Draft markdown files: `drafts/*.md`
- Assertions: `../checks/source_acquisition_request_draft_bundle_v1_assertions.out`
