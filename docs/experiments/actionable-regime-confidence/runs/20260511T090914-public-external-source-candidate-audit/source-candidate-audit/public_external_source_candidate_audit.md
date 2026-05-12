# Public External Source Candidate Audit

Run ID: `20260511T090914+0800-public-external-source-candidate-audit`

Board: Board A, `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Objective

Inspect public external candidates that might provide independent source-backed parent-root labels for active `MainRegimeV2` roots (`Bull`, `Bear`, `Sideways`, `Crisis`) or timestamped direct `Manipulation` positive/negative windows.

## Candidate Classification

| Candidate | Source | Decision | Reason |
|---|---|---|---|
| HuggingFace TSIE market regime dataset | `https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset` | `rejected_off_universe_rule_ohlcv_labels` | Public and ungated, but it is IDX/off-universe, uses rule-based price action/volatility/RSI/volume labels, does not provide exact requested instruments/timeframes, and has no `Crisis` root. |
| TRADEMEM market regime detection | `https://www.trademem.com/en/market-regime-detection` | `rejected_model_current_service_no_export_panel` | Describes real-time bull/bear/stagnant tag models and risk overlays, but no accepted historical exportable source-label panel for Board A slots. |
| GetRegime API | `https://getregime.com/api/v1/market/regime` | `blocked_cloudflare_current_service_no_rows` | Direct curl returned a Cloudflare challenge page rather than materialized JSON rows; even if accessible, this is a current-service surface, not a full historical label panel. |
| NBER business cycle dates | `https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions` | `sidecar_only_macro_cycle_not_price_root_panel` | Official peak/trough recession chronology is useful macro context, but it is not instrument-specific `Bull`/`Bear`/`Sideways`/`Crisis` price-root labeling for the requested provider/instrument/timeframe slots. |
| FRED USREC | `https://fred.stlouisfed.org/series/USREC` | `sidecar_only_recession_indicator_not_root_panel` | Monthly NBER-based recession indicator can support macro `Crisis` context, but cannot fill all parent roots or exact-underlying market slots. |
| GitHub code API probe | `https://api.github.com/search/code` | `blocked_unmaterialized_code_search` | Narrow unauthenticated code probes did not materialize a CSV/source-label panel in this environment; prior GitHub metadata search also found 0 accepted sources. |

## Result

- Public/external candidates inspected: `6`.
- Accepted independent MainRegimeV2 parent-root label sources: `0`.
- New attached parent-root source-label slots: `0`.
- Accepted direct `Manipulation` positive/negative rows/windows: `0`.
- Sidecar/provenance candidates retained: NBER/FRED macro recession chronology only.
- Accepted gate remains: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Gate result: `blocked_public_external_candidates_no_accepted_source_label_panel`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Obtain a downloadable or authenticated exact-underlying parent-root label panel for `Bull`/`Bear`/`Sideways`/`Crisis`, or authenticated timestamped direct `Manipulation` positive/negative rows. Do not spend more loops on public model/proxy/regime-indicator surfaces that do not expose exportable source labels.
