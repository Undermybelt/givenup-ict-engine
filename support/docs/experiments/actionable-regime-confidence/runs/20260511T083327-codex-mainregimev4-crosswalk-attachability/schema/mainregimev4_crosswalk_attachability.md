# MainRegimeV4 Crosswalk Attachability

Run id: `20260511T083327+0800-codex-mainregimev4-crosswalk-attachability`

## Result

- Active taxonomy: `MainRegimeV4`.
- V4 completion roots: `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, `Manipulation`.
- Accepted V4 completion roots added: `0`.
- Accepted V4 price-root source-label slots: `0`.
- Prior V2 exact-underlying candidate slots retained only for re-audit: `48/612`.
- Missing or rejected prior V2 slots still requiring external labels or V4 re-audit: `564/612`.
- Direct `Manipulation` new label sources added by the Dune/Mendeley source scan lane: `0`.
- Mendeley v3 Gox re-audit remains blocked: `blocked_mendeley_gox_hgb_wash_below_95`.
- Gate result: `blocked_mainregimev4_crosswalk_all_roots_need_reaudit_or_labels`.

## Crosswalk

| Prior root | V4 root | Handling |
|---|---|---|
| `Bull` | `BullExpansion` | `reaudit_required` |
| `Bear` | `BearExpansion` | `reaudit_required` |
| `Sideways` | `Consolidation` | `reaudit_required` |
| `Crisis` | `CrisisStress` | `preserved_provenance_reaudit_required` |
| `Manipulation` overlay | `Manipulation` | `active_root_output_direct_input_gate` |

## Accounting

- Existing MainRegimeV2 source-label attachability is provenance only until a V4 chronological calibration/test gate reruns.
- `Manipulation` keeps direct-event provenance from Mehrnoom/Mirtaheri (`test Wilson95 0.999700770660`), but V4 full direct-manipulation completion remains blocked because Mendeley failed coverage/ECE and Dune is not exported yet.
- Raw data committed: false. Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

## Next Action

Try a bounded Dune `nft.wash_trades` export path under the V4 `Manipulation` root with replayable timestamps, positive/negative windows, and provenance. Do not count rule-only labels or OHLCV proxies.
