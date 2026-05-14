# Zenodo DEX Self-Trade Direct Row Preflight

Run ID: `20260511T095606+0800-codex-zenodo-dex-selftrade-direct-row-preflight`

## Result

- Source: Zenodo record `4540223`, backed by `friedhelmvictor/lob-dex-wash-trading-paper`.
- Candidate direct `Manipulation` rows exported: `48`.
- Positive self-trade rows: `24`.
- Same-venue non-self negative controls: `24`.
- Accepted parent-root sources added: `0`.
- Accepted direct `Manipulation` rows added: `0`.
- Gate result: `blocked_candidate_direct_rows_exported_full_acceptance_gate_not_run`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Artifacts

- Candidate direct rows: `source-audit/direct_manipulation_rows_candidate_v1.csv`
- Audit JSON: `source-audit/zenodo_dex_selftrade_direct_row_preflight.json`
- Assertions: `checks/zenodo_dex_selftrade_direct_row_preflight_assertions.out`

## Notes

The source files are real DEX trade rows, but this run only streams enough rows to
create a replayable direct-row sample. It does not download or commit the 1-2GB
raw files and does not claim full chronological acceptance.

## Next Action

Run a full or larger bounded chronological Zenodo DEX direct gate from `/tmp`, or
continue acquisition for exact yfinance/Kraken parent-root labels.
