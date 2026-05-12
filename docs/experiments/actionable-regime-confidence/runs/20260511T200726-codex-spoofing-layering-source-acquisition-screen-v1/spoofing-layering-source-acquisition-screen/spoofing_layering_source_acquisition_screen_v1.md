# Spoofing/Layering Source Acquisition Screen v1

Run ID: `20260511T200726-codex-spoofing-layering-source-acquisition-screen-v1`

Focused follow-up to the `195728` strict acquisition contract and `200319` v26 completion audit. This screen targets only R6: source-owned spoofing/layering positives plus matched normal controls. Raw readbacks stayed under `/tmp/ict-engine-spoofing-layering-source-acquisition-screen-v1`; no raw data was committed.

## Decision

`spoofing_layering_source_acquisition_screen_v1=no_ready_positive_control_intake_source`

- Candidates screened: `5`.
- Ready positive/control intake sources found: `0`.
- Owner-approval/export target retained: `do_putnins_2023_detecting_layering_spoofing`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Direct species coverage closed: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Required Contract

- `row_level_direct_manipulation_positive_rows`
- `matched_same_schema_normal_controls`
- `source_owned_or_owner_approved_provenance`
- `venue_symbol_timestamp_fields`
- `chronological_validation_possible`
- `no_generated_proxy_synthetic_or_ohlcv_only_labels`

## Candidate Disposition

- `do_putnins_2023_detecting_layering_spoofing` (spoofing_layering): `blocked_owner_approval_or_export_required`. Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036. Reason: High-value owner/contact target, but no public owner-approved positive/control row package or provenance manifest was found.
- `delise_2023_deep_sad_tmx_fraud` (spoofing_layering_or_futures_fraud): `blocked_proprietary_no_public_rows`. Source: https://arxiv.org/abs/2309.00088. Reason: Real-label evidence exists in the paper, but the row panel is proprietary and not an exportable Board A intake package.
- `lin_2025_multilevel_manipulation_lob` (multilevel_spoofing_layering): `blocked_injected_synthetic_labels`. Source: https://arxiv.org/abs/2508.17086. Reason: Useful method source, but injected manipulation labels violate the no generated/synthetic label rule for strict direct species closure.
- `veryzhenko_spoofing_hft_ml` (spoofing_layering): `blocked_simulated_or_unreachable_source_rows`. Source: https://www.institutlouisbachelier.org/wp-content/uploads/2024/03/detecting-spoofing-in-high-frequency-trading-using-machine-learning-techniques.pdf. Reason: No reachable owner-approved real positive/control row package was found; simulated order-book evidence is disallowed for strict R6.
- `tao_day_ling_drapeau_2020_spoofing_hft` (spoofing_layering_pinging): `blocked_method_source_no_row_export`. Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3746263. Reason: Method/provenance only in public surfaces; no source-owned labeled positive/control rows or provenance manifest were found.

## Carry-Forward

The closest acquisition target is `do_putnins_2023_detecting_layering_spoofing`: it appears to have real prosecuted-case provenance and some order/trade-level granularity, but it still needs owner-approved export or author/regulator cooperation before Board A can materialize `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv`, matched controls, and `provenance_manifest.json`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T200726-codex-spoofing-layering-source-acquisition-screen-v1/spoofing-layering-source-acquisition-screen/spoofing_layering_source_acquisition_screen_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T200726-codex-spoofing-layering-source-acquisition-screen-v1/spoofing-layering-source-acquisition-screen/spoofing_layering_source_acquisition_screen_v1_candidates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T200726-codex-spoofing-layering-source-acquisition-screen-v1/checks/spoofing_layering_source_acquisition_screen_v1_assertions.out`
