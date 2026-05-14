# Direct Missing Species Source Screen v1

Run ID: `20260511T185706+0800-codex-direct-missing-species-source-screen-v1`

Supplemental public-source screen for missing direct `Manipulation` species: `quote_stuffing`, `pinging`, and `spoofing_layering`. It does not download raw rows, fill intake files, or edit Current Cursor.

## Decision

`direct_missing_species_source_screen_v1=no_ready_positive_control_source`

- Candidates screened: `7`.
- Ready real positive/control sources: `0`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full objective achieved: `false`; `update_goal=false`.

## Candidate Disposition

- `Learning from the Sequence of Order Events in the Stock Market` (spoofing_layering): `blocked_paper_method_no_exported_labeled_rows`. Source: https://arxiv.org/abs/2204.12270
- `FX spoofing and pinging case study` (spoofing_layering,pinging): `blocked_restricted_data_no_public_controls`. Source: https://www.sciencedirect.com/science/article/abs/pii/S0304405X21002368
- `Cross-market spoofing article` (spoofing_layering): `blocked_restricted_case_data_no_public_row_export`. Source: https://www.sciencedirect.com/science/article/pii/S1386418124000624
- `parasec Bitstamp spoofing visualisation` (spoofing_layering): `blocked_visual_case_no_machine_readable_labels_controls`. Source: https://parasec.net/transmission/order-book-visualisation/
- `codyrodgers/capstone-quote-stuffing` (quote_stuffing): `blocked_detection_project_no_source_owned_labels`. Source: https://github.com/codyrodgers/capstone-quote-stuffing
- `microalpha PyPI` (quote_stuffing,spoofing_layering): `blocked_feature_library_no_direct_labels`. Source: https://pypi.org/project/microalpha/
- `nguyentranai07/HTrade_Analyze_all` (quote_stuffing,spoofing_layering,pinging): `blocked_text_instruction_dataset_no_market_rows`. Source: https://huggingface.co/datasets/nguyentranai07/HTrade_Analyze_all

## Guardrail

Papers, case-study pages, feature libraries, demos, and text/instruction datasets can inform future probes, but Board A direct `Manipulation` still requires row-level positives, matched normal controls, provenance, and unchanged chronological/heldout validation before any 95% confidence claim.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T185706-codex-direct-missing-species-source-screen-v1/direct-missing-species-screen/direct_missing_species_source_screen_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T185706-codex-direct-missing-species-source-screen-v1/direct-missing-species-screen/direct_missing_species_source_screen_v1_candidates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T185706-codex-direct-missing-species-source-screen-v1/checks/direct_missing_species_source_screen_v1_assertions.out`
