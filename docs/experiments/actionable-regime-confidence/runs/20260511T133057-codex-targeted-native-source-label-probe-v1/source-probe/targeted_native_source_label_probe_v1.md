# Targeted Native Source-Label Probe v1

Run ID: `20260511T133057+0800-codex-targeted-native-source-label-probe-v1`

## Scope

This probe follows the current Board A next action: target unsupported intraday/full-species `MainRegimeV2` source-label cells and direct `Manipulation` matched-negative rows. It is not another broad source sweep.

## Result

- Accepted new native intraday/full-species parent-root source-label panels: `0`.
- Accepted direct `Manipulation` rows added: `0`.
- Useful acquisition target found: FINRA Potential Manipulation Report schema for spoofing/layering row exports.
- Gate result: `targeted_probe_no_new_attachable_native_source_label_panel_finra_schema_target_identified`.
- Full objective achieved: `false`.

## Candidate Decisions

| Source | Decision | Why |
|---|---|---|
| Kaggle Stock Market Regimes 2000-2026 | `already_consumed_same_source_daily_weekly_monthly_stock_index_panel` | It is the already accepted stock/index daily plus same-source `1w/1mo` panel; it does not add unsupported native intraday/full-species cells. |
| MarketIndicator.io RegimeScore | `rejected_model_output_not_independent_exact_label_panel` | Daily model score, not an exportable provider/instrument/timeframe panel with exact `Bull` / `Bear` / `Sideways` / `Crisis` source labels. |
| FINRA Potential Manipulation Report | `useful_schema_and_acquisition_target_not_public_rows` | Public page exposes spoofing/layering detail fields, but not exportable positive and matched negative rows. |
| lobflow | `rejected_detector_or_synthetic_proxy_not_direct_evidence_rows` | Detector confidence and synthetic rows cannot replace timestamped real positive/negative order-lifecycle labels. |
| ETF trend versus oscillation paper | `rejected_binary_research_label_not_exact_mainregimev2_panel` | Binary trend/oscillation research label, not a four-root `MainRegimeV2` panel or intraday/full-species source coverage. |

## Targeted Positive Path

- Price-root lane: continue with authenticated/user-provided source-label exports or explicit owner-approved crosswalks only.
- Direct `Manipulation` lane: FINRA spoofing/layering detail schema is the most concrete matched-negative acquisition target; public docs do not provide rows.

## Guardrails

- No runtime code changed.
- No thresholds relaxed.
- No raw data committed.
- No trade usability claimed.
- Proxy/model/synthetic sources remain rejected for completion.

## Sources

- Kaggle Stock Market Regimes 2000-2026: `https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026`
- MarketIndicator.io About: `https://www.marketindicator.io/about`
- FINRA Potential Manipulation Report: `https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report`
- lobflow: `https://pypi.org/project/lobflow/`
- ETF trend versus oscillation paper: `https://www.mdpi.com/1911-8074/19/4/262`
