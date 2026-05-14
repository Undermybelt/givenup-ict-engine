# R6 CourtListener RECAP Control Route After 080950 v1

- Run id: `20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1`.
- Case: `U.S. Commodity Futures Trading Commission v. Oystacher` / `1:15-cv-09196` / CourtListener docket `4263217`.
- Gate result: `r6_courtlistener_recap_control_route_after_080950_v1=public_recap_positive_and_context_only_no_source_owned_normal_controls`.
- Queries sent: `12`; query failures: `0`.
- RECAP documents scanned: `11`; available documents: `11`.
- Exhibit A attachment available: `True`.
- Defense expert report documents available: `2`.
- Source-owned normal-control documents found: `0`.
- Accepted rows added: `0`.
- Valid required-root unlock: `False`.
- Source/control evidence acquired: `False`.
- Canonical merge: `False`.
- Downstream promotion rerun: `False`.
- Strict full objective: `false`; trade usable: `false`; update_goal: `false`.

## Route Readback

The public RECAP route exposes the Oystacher docket and the Exhibit A attachment, plus defense expert-report and consent-order context. It does not expose an owner-approved normal/non-manipulation control export. The Exhibit A route remains positive/context evidence only under the current Board A contract because the known `FLIP` rows are same-defendant, same-exhibit sequence rows and still require explicit approval before they can serve as matched normal controls.

## Documents

- doc `1` attachment ``: complaint_context; available=True; pages=36; storage_head=429; COMPLAINT filed by U.S. Commodity Futures Trading Commission; Jury Demand. (Attachments: # 1 Exhibit A)(Streit, Elizabeth) (Entered: 10/19/2015)
- doc `1` attachment `1`: positive_exhibit_attachment_context; available=True; pages=116; storage_head=429; COMPLAINT filed by U.S. Commodity Futures Trading Commission; Jury Demand. (Attachments: # 1 Exhibit A)(Streit, Elizabeth) (Entered: 10/19/2015)
- doc `50` attachment ``: other_recap_context; available=True; pages=13; storage_head=429; MEMORANDUM Opinion and Order Signed by the Honorable Amy J. St. Eve on 12/18/2015:Mailed notice(kef, ) (Entered: 12/18/2015)
- doc `80` attachment ``: other_recap_context; available=True; pages=75; storage_head=429; Expert Report of Daniel R. Fischel by 3 Red Trading LLC, Igor B Oystacher (Liu, Kristina) (Entered: 03/17/2016)
- doc `84` attachment ``: defense_expert_report_context_not_source_owner_control; available=True; pages=26; storage_head=429; Supplemental Report of Daniel R. Fischel by 3 Red Trading LLC, Igor B Oystacher (Giannini, Jacqueline) (Entered: 03/22/2016)
- doc `85` attachment ``: defense_expert_report_context_not_source_owner_control; available=True; pages=26; storage_head=429; Supplemental Report of Daniel R. Fischel by 3 Red Trading LLC, Igor B Oystacher (Giannini, Jacqueline) (Entered: 03/23/2016)
- doc `134` attachment ``: other_recap_context; available=True; pages=60; storage_head=429; CORRECTED BESSEMBINDER REBUTTAL REPORT by U.S. Commodity Futures Trading Commission (Kramer, Jon) (Entered: 04/15/2016)
- doc `195` attachment ``: other_recap_context; available=True; pages=99; storage_head=429; MEMORANDUM Opinion and Order Signed by the Honorable Amy J. St. Eve on 7/12/2016:Mailed notice(kef, ) (Entered: 07/12/2016)
- doc `236` attachment ``: other_recap_context; available=True; pages=26; storage_head=429; MEMORANDUM Opinion and Order Signed by the Honorable Amy J. St. Eve on 8/23/2016:Mailed notice(kef, ) (Entered: 08/23/2016)
- doc `237` attachment ``: other_recap_context; available=True; pages=26; storage_head=429; CORRECTED MEMORANDUM Opinion and Order Signed by the Honorable Amy J. St. Eve on 8/23/2016: The conclusion has been amended in the Corrected Memorandum Opinion and Order to reflect
- doc `287` attachment ``: consent_order_context_not_row_control; available=True; pages=19; storage_head=429; CONSENT ORDER of Permanent Injunction, Civil Monetary Penalty, and Other Equitable Relief Against Igor B. Oystacher and 3 Red Trading LLC Signed by the Honorable Amy J. St. Eve on 

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1/r6-courtlistener-recap-control-route-after-080950-v1/r6_courtlistener_recap_control_route_after_080950_v1.json`
- Request CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1/r6-courtlistener-recap-control-route-after-080950-v1/r6_courtlistener_recap_control_route_requests_v1.csv`
- Document CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1/r6-courtlistener-recap-control-route-after-080950-v1/r6_courtlistener_recap_control_route_documents_v1.csv`
- HEAD CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1/r6-courtlistener-recap-control-route-after-080950-v1/r6_courtlistener_recap_control_route_head_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1/checks/r6_courtlistener_recap_control_route_after_080950_v1_assertions.out`

## Next

Continue source/control acquisition only. The live unlock remains one of: owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE/exchange order-lifecycle export with positives and matched normal controls; or explicit approval of the same-exhibit `FLIP`-as-control exception. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion from this route.
