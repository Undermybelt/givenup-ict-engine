# R6 Public Docket Attachment Route Probe After 080700 v1

- Run id: `20260512T081149+0800-codex-r6-public-docket-attachment-route-probe-after-080700-v1`.
- Gate result: `r6_public_docket_attachment_route_probe_after_080700_v1=no_new_public_docket_control_attachment_no_unlock`.
- Requests sent: `17`.
- CourtListener storage PDFs reachable: `2`.
- CourtListener storage PDFs acquired: `2`.
- CourtListener docket/API accessible: `false`.
- Independent public normal-control documents found: `0`.
- Prior Exhibit A materialization rows: `6735` with side counts `{'SPOOF': 5182, 'FLIP': 1553}`.
- Accepted rows added: `0`; valid required-root unlock: `false`; source/control evidence acquired: `false`; `update_goal=false`.

## Interpretation

The public CourtListener storage route yields docket document `1.0` and attachment `1.1` from cached/live public storage. The reachable `1.1` attachment is the already materialized Exhibit A source containing `SPOOF` and `FLIP` labels, not an independent normal-control export. Current sibling/docket/API/official-public probes do not add verifier-native matched normal-control rows.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T081149+0800-codex-r6-public-docket-attachment-route-probe-after-080700-v1/r6-public-docket-attachment-route-probe-after-080700-v1/r6_public_docket_attachment_route_probe_after_080700_v1.json`
- Request CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T081149+0800-codex-r6-public-docket-attachment-route-probe-after-080700-v1/r6-public-docket-attachment-route-probe-after-080700-v1/r6_public_docket_attachment_route_requests_v1.csv`
- Document CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T081149+0800-codex-r6-public-docket-attachment-route-probe-after-080700-v1/r6-public-docket-attachment-route-probe-after-080700-v1/r6_public_docket_attachment_route_documents_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T081149+0800-codex-r6-public-docket-attachment-route-probe-after-080700-v1/checks/r6_public_docket_attachment_route_probe_after_080700_v1_assertions.out`

## Next

Continue source/control acquisition only: use owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE/exchange order-lifecycle exports with positives plus matched normal controls, or obtain explicit approval for the same-exhibit `FLIP` control exception before any verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.
