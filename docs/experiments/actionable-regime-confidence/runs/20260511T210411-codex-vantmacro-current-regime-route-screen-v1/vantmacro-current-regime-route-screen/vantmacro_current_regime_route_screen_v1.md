# VantMacro Current Regime Route Screen v1

- Gate result: `vantmacro_current_regime_route_screen_v1=source_route_found_rows_not_acquired`.
- Public URL: `https://vantmacro.com/`.
- HTTP status: `200`; bytes: `132432`.
- Text checks: `{"mentions_2003_2026": true, "mentions_current_regime": true, "mentions_daily_weekly": true, "mentions_dashboard": true, "mentions_market_regime": true, "mentions_pro": true}`.
- Rows acquired: `false`; intake files created: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Boundary

This is a route screen only. The page is a plausible source-owner/contact or product route for current macro/asset regime labels, but this run did not acquire row-level labels, MainRegimeV2 crosswalks, split roles, or provenance hashes. The source-label equivalence intake verifier remains fail-closed.

## Verifier Readback

- Status: `blocked`.
- Reason: `missing_required_files`.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T210411-codex-vantmacro-current-regime-route-screen-v1/vantmacro-current-regime-route-screen/vantmacro_current_regime_route_screen_v1.json`
- Candidate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T210411-codex-vantmacro-current-regime-route-screen-v1/vantmacro-current-regime-route-screen/vantmacro_current_regime_route_screen_v1_candidates.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T210411-codex-vantmacro-current-regime-route-screen-v1/checks/vantmacro_current_regime_route_screen_v1_assertions.out`
