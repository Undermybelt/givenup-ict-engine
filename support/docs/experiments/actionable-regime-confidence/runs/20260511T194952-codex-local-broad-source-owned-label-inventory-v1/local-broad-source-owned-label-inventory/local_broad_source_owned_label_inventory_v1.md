# Local Broad Source-Owned Label Inventory v1

- Decision: `local_broad_source_owned_label_inventory_v1=no_new_promotable_uncounted_source_owned_labels`
- Matched local files: `8962`
- Candidate groups: `7`
- Accepted rows added: `0`
- New confidence gate: `false`
- Strict full objective achieved: `false`; `update_goal=false`

This bounded inventory searched likely local data roots for un-packaged source-owned regime labels or direct manipulation rows. It is broader than the exact intake filename rescan, but it still does not promote generated labels, duplicate source-panel rows, raw provider panels, code repos, or already registered Board A artifacts. The inventory uses path and header rules only; ambiguous files remain blocked unless a source-owned schema/provenance package is supplied.

## Group Disposition

| Group | Files | Label-like CSV headers | Exact intake filename hits | Disposition | Reason |
|---|---:|---:|---:|---|---|
| `direct_pump_dump_raw_windows` | `978` | `0` | `0` | `raw_or_event_window_pump_dump_not_missing_species` | Raw/event-window crypto pump/dump files are not source-owned rows for the missing direct manipulation species and do not provide spoofing/layering controls. |
| `direct_pump_dump_telegram` | `11` | `1` | `0` | `known_scoped_direct_pump_dump_already_counted` | Telegram pump/dump direct rows support the already accepted scoped pump_dump variety, but they do not cover spoofing/layering, quote stuffing, pinging, bear raid, or matched negative controls. |
| `generated_or_model_derived_regime_outputs` | `86` | `0` | `0` | `generated_proxy_outputs_rejected` | Model outputs and prior experiment predictions are not source-owned active-regime labels for strict Board A completion. |
| `local_spoofing_repo_quantsingularity` | `3` | `0` | `0` | `code_or_synthetic_surface_not_source_owned_rows` | Local spoofing repo contains code, config, or synthetic generation surfaces; no exportable real positive rows plus matched controls are present. |
| `other_local_hits` | `6069` | `37` | `0` | `not_promotable_by_path_header_inventory` | Filename matched broad keywords but did not expose an exact Board A intake file, known source-owned schema path, or missing-species positive/control package under this bounded path/header inventory. |
| `repo_existing_board_artifacts` | `1801` | `118` | `0` | `already_registered_board_artifacts` | Existing Board A artifacts are already counted or rejected; they are not new intake rows. |
| `stock_market_regimes_source_panel` | `14` | `3` | `0` | `known_source_daily_already_counted` | Daily MainRegimeV2 source panel is already counted by the strict gate; local duplicates do not add strict 1h, native sub-hour, recency-tail, or other-market equivalence rows. |

## Requirement Readback

| Requirement | Status | Evidence |
|---|---|---|
| `R2` Other-cycle/timeframe validation has suitable confidence | `fail_blocked` | Local inventory found no uncounted source-owned strict 1h or native sub-hour label rows. |
| `R3` Strict 1h next-source intake has source-owned rows and provenance | `fail_blocked` | No local source_label_equivalence_rows.csv or equivalent uncounted package found. |
| `R5` XOM/Sideways recency-tail repair rows exist | `fail_blocked` | Only known stock-market-regimes source panel duplicates were found; no uncounted recency-tail source rows. |
| `R6` Native sub-hour source labels exist | `fail_blocked` | Local hits were generated/model/code/raw-provider surfaces or already registered projections; none are source-owned native sub-hour labels. |
| `R7` Other-market/source-label equivalence has suitable confidence | `fail_blocked` | No owner-approved MainRegimeV2 equivalence package found outside existing Board A artifacts. |
| `R8` Direct Manipulation has full species coverage with real positives and matched controls | `fail_blocked` | Local direct hits only cover already scoped pump/dump or code/synthetic/raw surfaces; no missing species positive/control package found. |

## Artifacts

- JSON: `local_broad_source_owned_label_inventory_v1.json`
- Groups CSV: `local_broad_source_owned_label_inventory_v1_groups.csv`
- Candidate sample CSV: `local_broad_source_owned_label_inventory_v1_candidates.csv`
- Requirements CSV: `local_broad_source_owned_label_inventory_v1_requirements.csv`
