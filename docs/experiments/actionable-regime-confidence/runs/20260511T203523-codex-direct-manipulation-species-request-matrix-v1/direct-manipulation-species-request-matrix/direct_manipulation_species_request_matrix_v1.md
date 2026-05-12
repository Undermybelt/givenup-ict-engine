# Direct Manipulation Species Request Matrix v1

Run ID: `20260511T203523-codex-direct-manipulation-species-request-matrix-v1`

- Gate result: `direct_manipulation_species_request_matrix_v1=request_ready_rows_not_acquired`.
- Purpose: convert the remaining direct Manipulation species blocker into an owner/export request matrix without promoting raw LOB, paper, method, or library surfaces.
- Candidate rows consumed: `7`.
- Matrix rows written: `14`.
- Target species: `spoofing_layering, quote_spoofing, quote_stuffing, pinging, bear_raid, painting_tape`.
- Current intake root: `/tmp/ict-engine-direct-manipulation-row-intake`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Species Summary

| Species | Candidate surfaces | Positive surface | Matched controls | Provenance surface | Gate |
|---|---:|---|---|---|---|
| `spoofing_layering` | `6` | `true` | `false` | `true` | `blocked` |
| `quote_spoofing` | `1` | `true` | `false` | `false` | `blocked` |
| `quote_stuffing` | `3` | `true` | `false` | `true` | `blocked` |
| `pinging` | `2` | `true` | `false` | `true` | `blocked` |
| `bear_raid` | `0` | `false` | `false` | `false` | `blocked` |
| `painting_tape` | `0` | `false` | `false` | `false` | `blocked` |

## Boundary

- This run does not send requests, create intake rows, change verifiers, or claim direct `Manipulation` completion.
- Raw order-book providers can support controls or future probes, but cannot satisfy Board A without source-owned positive labels and matched controls.
- Paper/method/library surfaces remain provenance for request language only.

## Artifacts

- JSON: `direct_manipulation_species_request_matrix_v1.json`
- Matrix CSV: `direct_manipulation_species_request_matrix_v1.csv`
- Species summary CSV: `direct_manipulation_species_summary_v1.csv`
- Required fields CSV: `direct_manipulation_species_required_fields_v1.csv`
- Request template: `direct_manipulation_species_request_template_v1.md`
- Assertions: `../checks/direct_manipulation_species_request_matrix_v1_assertions.out`
