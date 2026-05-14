# Do/Putnins Contact Leads v1

Run ID: `20260511T201759-codex-do-putnins-contact-leads-v1`

- Gate result: `do_putnins_contact_leads_v1=public_contact_paths_ready_rows_not_acquired`.
- Purpose: turn the `201352` owner-request template into executable public contact leads for the closest R6 spoofing/layering owner target.
- Request sent: `false`; rows acquired: `false`; accepted rows added: `0`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Source Target

- Target: `do_putnins_2023_detecting_layering_spoofing` / `Detecting Layering and Spoofing in Markets`.
- Primary source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036.
- Request template: `docs/experiments/actionable-regime-confidence/runs/20260511T201352-codex-do-putnins-owner-request-package-v1/do-putnins-owner-request-package/do_putnins_owner_request_template_v1.md`.

## Public Contact Leads

- `ssrn_author_email_links`: SSRN abstract page author email links (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036) -> `ready_contact_surface_no_rows_acquired`. Use the page's public author email links to send the owner-request template.
- `ssrn_contact_author`: SSRN contact author listing for Bao Linh Do (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036) -> `ready_contact_surface_no_rows_acquired`. Ask whether an owner-approved, redacted positive/control row package can be exported for Board A verifier intake.
- `uts_talis_putnins_profile`: UTS public profile for Talis Putnins (https://profiles.uts.edu.au/talis.putnins) -> `ready_contact_surface_no_rows_acquired`. Secondary author/institutional route if SSRN author email links are unavailable.
- `repec_author_record`: RePEc author-paper record (https://ideas.repec.org/p/arx/papers/2308.00198.html) -> `bibliographic_fallback_no_rows_acquired`. Bibliographic fallback to confirm paper identity and author linkage before sending the request.

## Boundary

This run does not send a request and does not create intake rows. It only identifies public contact surfaces for a human or authenticated follow-up. Rows remain unacceptable until an owner-approved package lands under `/tmp/ict-engine-direct-manipulation-row-intake` and passes the existing verifier.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T201759-codex-do-putnins-contact-leads-v1/do-putnins-contact-leads/do_putnins_contact_leads_v1.json`
- Contact CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T201759-codex-do-putnins-contact-leads-v1/do-putnins-contact-leads/do_putnins_contact_leads_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T201759-codex-do-putnins-contact-leads-v1/checks/do_putnins_contact_leads_v1_assertions.out`
