# R6 Owner Export Dispatch Feasibility Readback v1

Run id: `20260512T055516-codex-r6-owner-export-dispatch-feasibility-readback-v1`

Gate result: `r6_owner_export_dispatch_feasibility_readback_v1=drafts_parseable_not_sent_no_transport_identity_no_rows`

## Scope

Read-only feasibility check for the existing `052650` v5 CME/Cboe/CFE owner-export `.eml` drafts. This run does not send external email, receive ticket/export/license identifiers, acquire verifier-native rows, mutate target roots, approve `FLIP` controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- Drafts parseable: `true`.
- CLI transport binaries present: `true` (`sendmail=/usr/sbin/sendmail`, `mail=/usr/bin/mail`).
- Explicit user mail config present: `false`.
- Sender identity in drafts: `false`.
- External requests sent: `false`.

## Decision

The existing v5 drafts are ready for an operator-controlled dispatch path, but this machine state is not enough to send them unattended: drafts have no `From` header and no user-level `msmtp`/`mutt`/mail config was found. This readback therefore does not unlock R6 or downstream promotion.

Required roots remain absent unless the JSON says otherwise:

- `/tmp/ict-engine-board-a-r6-owner-export-v1`
- `/tmp/ict-engine-native-subhour-source-label-intake`
- `/tmp/ict-engine-source-panel-recency-extension`

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Send the existing `.eml` drafts only through an approved operator mail path, preserving ticket/export/license/order/support identifiers in provenance. Continue Board A only after explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root.
