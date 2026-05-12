# Native Subhour Overlap Blocker v1

Run ID: `20260511T180420+0800-codex-native-subhour-overlap-blocker-v1`

This is a compact overlap probe for the P1 native sub-hour blocker. It fetches at most two source-panel markets and two native sub-hour timeframes, keeps raw provider rows out of the repo, and does not generate labels.

## Result

- Cells checked: `4` (`AAPL, ^IXIC` x `15m, 30m`).
- Ready overlap cells: `0`.
- Blocked cells: `4`.
- Source panel max date: `2026-01-30`.
- Provider native sub-hour rows were current-window only for this probe, so they did not overlap the source-label tail.
- Accepted rows added: `0`.
- Gate result: `native_subhour_overlap_blocker_v1=no_source_overlap_0of4_cells`.
- Full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Cells

| Symbol | Timeframe | Provider Rows | Provider Dates | Source Dates | Overlap Sessions | State | Blocker |
|---|---|---:|---|---|---:|---|---|
| `AAPL` | `15m` | 1560 | `2026-02-12` to `2026-05-08` | `2000-01-03` to `2026-01-30` | 0 | `ready` | `no_provider_session_overlap_with_source_panel_tail` |
| `AAPL` | `30m` | 780 | `2026-02-12` to `2026-05-08` | `2000-01-03` to `2026-01-30` | 0 | `ready` | `no_provider_session_overlap_with_source_panel_tail` |
| `^IXIC` | `15m` | 1560 | `2026-02-12` to `2026-05-08` | `2000-01-03` to `2026-01-30` | 0 | `ready` | `no_provider_session_overlap_with_source_panel_tail` |
| `^IXIC` | `30m` | 780 | `2026-02-12` to `2026-05-08` | `2000-01-03` to `2026-01-30` | 0 | `ready` | `no_provider_session_overlap_with_source_panel_tail` |

## Next

Use `source_panel_recency_extension_manifest_v1` first. Native sub-hour calibration should remain blocked until source-owned rows after `2026-01-30` exist and pass the recency verifier.
