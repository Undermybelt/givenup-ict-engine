# CourtListener RECAP Sibling Fast Probe After 081323 v1

Gate result: `courtlistener_recap_sibling_fast_probe_after_081323_v1=no_new_public_control_attachment_unlock`.

## Scope

Fast bounded replacement for the nonterminal `081323` script-only run. This probes the same
CourtListener RECAP docket storage namespace using concurrent short-timeout HEAD checks.
It does not download PDFs into the repo, approve RECAP/PACER provenance, approve same-exhibit
`FLIP` rows as controls, mutate any intake root, or run downstream promotion.

## Metrics

- Requests sent: `402`
- Failed or parse-failed: `3`
- CourtListener API status: `401`
- Public docket HTML status: `403`
- Storage HEAD requests: `400`
- Storage PDF hits: `0`
- Known Exhibit A present: `False`
- Novel public PDF hits: `0`
- Possible control-name hits: `0`

## Decision

No new public normal-control or matched-control attachment was acquired. Public RECAP
storage metadata remains non-unlocking without explicit provenance approval and without
source-owned normal controls.

Accepted rows added `0`; valid required-root unlock false; source/control evidence
acquired false; canonical merge false; selected-data AutoQuant promotion false;
downstream promotion rerun false; strict full objective false; trade usable false;
`promotion_allowed=false`; `update_goal=false`.

## Next

Continue source/control acquisition only, or obtain explicit user/board approval for the
same-exhibit `FLIP` control exception before canonical merge and downstream rerun.
