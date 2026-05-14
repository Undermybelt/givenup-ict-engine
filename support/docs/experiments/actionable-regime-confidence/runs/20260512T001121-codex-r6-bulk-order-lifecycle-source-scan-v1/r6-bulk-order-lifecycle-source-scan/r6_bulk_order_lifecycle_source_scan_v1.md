# R6 Bulk Order-Lifecycle Source Scan v1

Run ID: `20260512T001121-codex-r6-bulk-order-lifecycle-source-scan-v1`

## Scope

This is a targeted source scan after `r6_split_species_gap_impact_v1` showed that the remaining sidecars cannot close the current exact chronological/symbol/venue split gates. It does not mutate `/tmp/ict-engine-direct-manipulation-row-intake`, does not accept sidecar rows, and does not claim a Board A confidence gate.

## Result

- Public bulk order-lifecycle sources found in this scan are not sufficient for R6 strict acceptance.
- FINRA Potential Manipulation Report remains the closest source class, but it is an authenticated report/export path, not a public bulk row download in this environment.
- Nasdaq TotalView-ITCH / order-by-order sources can supply normal order-lifecycle controls, but they do not supply manipulation-positive labels.
- Public CFTC enforcement material can supply source-owned positive examples, but it remains sparse case evidence and does not provide bulk matched normal controls.
- Public/research datasets found by broad search are either synthetic, unlabeled, non-order-lifecycle, or not source-owned positive-plus-control exports.

## Source Classes Checked

| Source class | Observed utility | R6 acceptance status |
|---|---|---|
| FINRA Potential Manipulation Report (`https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report`) | Authenticated/export-style direct manipulation report source class | `owner_export_required` |
| Nasdaq TotalView-ITCH / order-by-order feeds (`https://www.nasdaqtrader.com/Trader.aspx?id=TotalViewITCH`) | Real order-lifecycle normal-market controls | `controls_only_no_positive_labels` |
| CFTC enforcement orders/complaints (`https://www.cftc.gov/LawRegulation/Enforcement/EnforcementActions/index.htm`) | Official sparse positive examples | `positive_inventory_not_bulk_split_support` |
| Public Kaggle/HuggingFace/research LOB datasets | Public data or papers, often unlabeled/synthetic | `not_accepted_for_direct_positive_rows` |

## Gate

- Gate result: `r6_bulk_order_lifecycle_source_scan_v1=public_bulk_source_not_found_owner_export_or_protocol_pivot_required`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Shared intake mutated: `false`.
- External requests sent: `true`, limited to source discovery.
- Trade usable: `false`.

## Next

Do not keep adding sparse sidecar case examples as if they can satisfy exact split validation. Either obtain an owner-approved/authenticated FINRA, venue-surveillance, CAT-like, or exchange order-lifecycle export with both positive rows and matched normal controls, or predeclare a less fragmented family-level validation protocol before the next R6 acceptance rerun.
