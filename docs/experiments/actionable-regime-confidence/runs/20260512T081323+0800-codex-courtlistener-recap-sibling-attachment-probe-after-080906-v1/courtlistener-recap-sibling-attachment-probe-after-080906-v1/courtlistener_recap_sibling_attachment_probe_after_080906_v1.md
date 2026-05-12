# CourtListener RECAP Sibling Attachment Probe After 080906 v1

Gate result: `courtlistener_recap_sibling_attachment_probe_after_080906_v1=no_new_public_control_attachment_unlock`.

## Scope

Bounded public RECAP storage sibling-object probe for the Oystacher/3Red docket after
the `080906` OpenAlex/Semantic/PapersWithCode route probe. This checks whether direct
CourtListener storage exposes adjacent public PDF objects beyond the already-known
Exhibit A PDF. It does not download raw PDFs into the repo, approve RECAP/PACER
provenance, approve `FLIP` rows as controls, mutate any intake root, or run downstream
promotion.

## Metrics

- Requests sent: `122`
- Failed or parse-failed: `0`
- CourtListener API status: `401`
- Public docket HTML status: `403`
- Storage HEAD requests: `120`
- Storage PDF hits: `2`
- Known Exhibit A present: `True`
- Novel public PDF hits: `1`
- Possible control-name hits: `0`
- Novel public PDF body classification attempt: `429` rate-limited in `/tmp`, so no text classification was accepted

## Decision

The storage scan found the known Exhibit A PDF and one adjacent public PDF metadata hit:
`gov.uscourts.ilnd.316889.1.0.pdf`. Filename and HEAD metadata alone do not identify a
source-owned normal-control or matched-control attachment. A follow-up `/tmp` body fetch
was rate-limited with HTTP `429`, so no text classification was accepted. No new public
normal-control or matched-control attachment was acquired. API/HTML routes were not
usable without authentication or were blocked by the serving layer, and direct storage
metadata does not satisfy the owner/export control contract.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3
native-subhour unlock false; valid required-root unlock false; source/control evidence
acquired false; canonical merge false; selected-data AutoQuant promotion false;
downstream promotion rerun false; strict full objective false; trade usable false;
`update_goal=false`.

## Next

Continue source/control acquisition only. The active R6 route still requires explicit
public RECAP/PACER provenance plus `FLIP`-as-control approval, or independent
source-owned normal controls, before any canonical merge or downstream rerun.
