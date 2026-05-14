# Post 081705 Required Root Dispatch Gate v1

Run id: `20260512T082337+0800-codex-post-081705-required-root-dispatch-gate-v1`

Gate result: `post_081705_required_root_dispatch_gate_v1=no_required_root_or_dispatch_unlock`

Board sha256 before artifact: `fd177408440b69c09e6d047283545afada629b711fa7bd92ec712ac66d787038`

## Purpose

Read-only gate check after the terminal public docket/RECAP probes. This packet checks whether any required R6 owner-export, R5 recency-extension, or R3 native-subhour source-label root arrived, and whether the v5 owner-export dispatch drafts are still intact. It does not send external messages, approve same-exhibit `FLIP` rows, mutate intake roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Latest Evidence Checked

| id | root exists | assertions exists | gate | accepted rows |
|---|---:|---:|---|---:|
| `081025` | `True` | `True` | `r6_direct_intake_approval_gap_readback_after_080950_v1=direct_intake_present_but_no_r6_owner_export_or_approval_unlock` | `` |
| `081149` | `True` | `True` | `r6_public_docket_attachment_route_probe_after_080700_v1=no_new_public_docket_control_attachment_no_unlock` | `0` |
| `081323` | `True` | `True` | `courtlistener_recap_sibling_attachment_probe_after_080906_v1=no_new_public_control_attachment_unlock` | `0` |
| `081522` | `True` | `True` | `r6_courtlistener_recap_control_route_after_080950_v1=public_recap_positive_and_context_only_no_source_owned_normal_controls` | `0` |
| `081705` | `True` | `True` | `courtlistener_recap_sibling_fast_probe_after_081323_v1=no_new_public_control_attachment_unlock` | `0` |

## Required Root Readback

| root | exists | all required files | approval present | visible files |
|---|---:|---:|---:|---:|
| `r6_owner_export` | `False` | `False` | `False` | `0` |
| `r5_recency` | `False` | `False` | `False` | `0` |
| `r3_native_subhour` | `True` | `True` | `False` | `2` |

## Dispatch Draft Integrity

| owner | exists | sha256 matches expected | status |
|---|---:|---:|---|
| `cme_group` | `True` | `True` | `draft_present_not_sent` |
| `cboe_cfe` | `True` | `True` | `draft_present_not_sent` |

## Decision

- R6 owner/export unlock: `False`.
- R5 recency unlock: `False`.
- R3 native-subhour unlock: `False`.
- Source/control evidence acquired: `False`.
- Canonical merge: `False`.
- Downstream promotion rerun: `False`.
- Strict full objective: `False`.
- `update_goal`: `False`.

## Next

Use an approved operator path to send/upload the v5 CME and Cboe/CFE drafts, preserve ticket/export/license identifiers, or supply explicit FLIP-control approval or verifier-native owner-export/source-panel/native-subhour rows before canonical merge or downstream rerun.
