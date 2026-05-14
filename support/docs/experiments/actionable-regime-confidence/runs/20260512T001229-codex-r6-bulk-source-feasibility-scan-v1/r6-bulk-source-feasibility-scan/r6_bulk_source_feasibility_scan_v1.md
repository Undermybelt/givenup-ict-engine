# R6 Bulk Source Feasibility Scan v1

- Run id: `20260512T001229-codex-r6-bulk-source-feasibility-scan-v1`
- V59 debt source: `docs/experiments/actionable-regime-confidence/runs/20260512T000801-codex-r6-exact-split-support-debt-audit-v1/r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json`
- Direct verifier status: `schema_ready_unscored`; positives `73`, matched negatives `73`.
- V59 chronological additional-row debt: `219` before exact symbol/venue gates.
- V59 exact-symbol pairwise debt: `2559`; exact-venue pairwise debt: `732`.
- Sources screened: `5`; ready-now public bulk source count: `0`; owner-export candidate count: `1`.
- Gate result: `r6_bulk_source_feasibility_scan_v1=no_public_ready_bulk_export_finra_owner_export_or_contract_reset_required`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.

## Source Decisions

| Source | Ready Now | Owner Export Candidate | R6 Fit | Blocker |
|---|---:|---:|---|---|
| `finra_potential_manipulation_report` | `false` | `true` | `equities_not_current_futures_buckets` | Requires owner/firm FINRA Report Center export; asset class is equities, so current futures exact-symbol/venue buckets would need a predeclared cross-market direct-Manipulation mapping. |
| `cftc_public_market_data_and_enforcement_pdfs` | `false` | `false` | `case_examples_only` | Public CFTC pages provide reports and enforcement PDFs, but not a downloadable balanced order-lifecycle export with hundreds of matched labeled spoof/non-spoof rows. |
| `tardis_exchange_order_book_data` | `false` | `false` | `controls_or_weak_labels_only` | Can supply depth/trade/order-book style bulk controls, but does not source-own spoofing/manipulation positives required by the direct evidence gate. |
| `polymarket_l2_orderbook_kaggle` | `false` | `false` | `prediction_market_controls_or_weak_labels_only` | Bulk L2/order-book data is useful for controls or research, but it is not source-owned manipulation-positive labeling for current R6 futures/order-lifecycle exact buckets. |
| `brogaard_hendershott_riordan_spoofing_study` | `false` | `false` | `evidence_that_needed_source_is_proprietary` | Study indicates the relevant order-level manipulation evidence exists in proprietary/regulatory data, but does not provide a public row export for Board A ingestion. |

## Interpretation

- No unauthenticated/public source in this bounded screen is ready to close the current R6 exact chronological/symbol/venue gates.
- FINRA Potential Manipulation Report is the only credible bulk labeled-source candidate, but it requires owner/firm export and likely a predeclared equities-to-direct-Manipulation validation mapping.
- Tardis and Polymarket-style L2/order-book datasets can help build controls or weak-label research, but they do not source-own the manipulation-positive labels required by the current Board A direct evidence gate.
- Existing public CFTC PDFs remain useful for precise row examples, not for the hundreds to thousands of matched rows quantified by V59.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T001229-codex-r6-bulk-source-feasibility-scan-v1/r6-bulk-source-feasibility-scan/r6_bulk_source_feasibility_scan_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260512T001229-codex-r6-bulk-source-feasibility-scan-v1/r6-bulk-source-feasibility-scan/r6_bulk_source_feasibility_scan_v1.md`
- Source CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001229-codex-r6-bulk-source-feasibility-scan-v1/r6-bulk-source-feasibility-scan/r6_bulk_source_feasibility_sources_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T001229-codex-r6-bulk-source-feasibility-scan-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T001229-codex-r6-bulk-source-feasibility-scan-v1/checks/r6_bulk_source_feasibility_scan_v1_assertions.out`
