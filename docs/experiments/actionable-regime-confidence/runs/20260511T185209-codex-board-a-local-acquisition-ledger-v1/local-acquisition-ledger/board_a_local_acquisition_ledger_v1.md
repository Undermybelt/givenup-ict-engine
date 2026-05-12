# Board A Local Acquisition Ledger v1

Run ID: `20260511T185209-codex-board-a-local-acquisition-ledger-v1`

Supplemental Board A ledger only. It registers completed concurrent blocker readbacks and checks local acquisition roots for ready source-owned intake files.

## Readbacks

- `20260511T184630-codex-direct-manipulation-coverage-readback-v2`: `direct_manipulation_coverage_readback_v2=scoped_varieties_present_full_species_blocked`; registered before this ledger: `false`.
- `20260511T184856-codex-source-label-other-market-readback-v1`: `source_label_other_market_readback_v1=partial_sources_no_full_equivalence`; registered before this ledger: `true`.

## Local Acquisition Check

- Required intake files present: `0/12`; missing: `12`.
- Local relevant candidate files scanned: `515`.
- Existing stock-regime source-panel files found: `4`; these are already-known source panels, not new other-market equivalence rows.
- Data files needing schema/owner match: `179`.

## Decision

`board_a_local_acquisition_ledger_v1=readbacks_registered_no_ready_local_intake`

- Unregistered completed readbacks before this ledger: `1`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T185209-codex-board-a-local-acquisition-ledger-v1/local-acquisition-ledger/board_a_local_acquisition_ledger_v1.json`
- Readbacks CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T185209-codex-board-a-local-acquisition-ledger-v1/local-acquisition-ledger/board_a_local_acquisition_readbacks_v1.csv`
- Intake files CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T185209-codex-board-a-local-acquisition-ledger-v1/local-acquisition-ledger/board_a_local_acquisition_intake_files_v1.csv`
- Local candidates CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T185209-codex-board-a-local-acquisition-ledger-v1/local-acquisition-ledger/board_a_local_acquisition_candidates_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T185209-codex-board-a-local-acquisition-ledger-v1/checks/board_a_local_acquisition_ledger_v1_assertions.out`
