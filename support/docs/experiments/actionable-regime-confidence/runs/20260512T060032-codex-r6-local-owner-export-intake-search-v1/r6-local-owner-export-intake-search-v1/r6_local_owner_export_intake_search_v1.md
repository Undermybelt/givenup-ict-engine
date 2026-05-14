# R6 Local Owner Export Intake Search v1

Run id: `20260512T060032-codex-r6-local-owner-export-intake-search-v1`

Gate result: `r6_local_owner_export_intake_search_v1=no_local_owner_export_or_control_rows_no_promotion`

## Scope

Bounded local search for existing CME/Cboe/CFE/Oystacher owner-export or normal-control files. This run does not send email, copy files into target roots, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Counts

- Files visited: `25000`.
- Keyword candidates: `130`.
- Manual-review candidates: `5`.
- Possible control files: `0`.

## Decision

No local file was promoted into the R6 owner-export target root. Any candidate that looks relevant is only a manual-review/source-approval candidate, not accepted source/control evidence.

Required roots remain absent unless the JSON says otherwise:

- `/tmp/ict-engine-board-a-r6-owner-export-v1`
- `/tmp/ict-engine-native-subhour-source-label-intake`
- `/tmp/ict-engine-source-panel-recency-extension`

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Dispatch the existing v5 `.eml` drafts only through an approved operator mail path, preserving ticket/export/license/order/support identifiers in provenance; otherwise continue only after explicit source/control approval or verifier-native R6 owner-export rows with valid controls unlock a required target root.
