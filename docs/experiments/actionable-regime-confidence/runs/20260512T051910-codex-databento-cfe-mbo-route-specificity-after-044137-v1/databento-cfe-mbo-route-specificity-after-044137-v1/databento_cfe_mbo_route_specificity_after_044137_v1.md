# Databento CFE MBO Route Specificity After 044137 v1

Run id: `20260512T051910-codex-databento-cfe-mbo-route-specificity-after-044137-v1`

Gate result: `databento_cfe_mbo_route_specificity_after_044137_v1=route_specificity_confirmed_no_local_export_no_promotion`

Generated at local time: `2026-05-12T05:19:10+0800`

## Purpose

Refine the already-counted `044137` official CME/Cboe/Databento route recheck with the current Databento CFE-specific route details. This packet records acquisition-route specificity only. It does not acquire licensed rows, create source-owned normal controls, mutate target roots, approve same-exhibit `FLIP` controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Route Specificity Readback

| Route | Current readback | Board A effect |
|---|---|---|
| Databento CFE announcement | Databento announced CFE coverage on `2026-04-15`; CFE historical coverage begins on `2018-11-04`; CFE data is sourced from the primary CFE Multicast PITCH feed; dataset id is `XCBF.PITCH`; the example request is for MBO/L3 VIX futures data. | This makes the CFE branch more concrete for post-2018 VIX/CFE depth/order-book acquisition, but it is still an external vendor/API route until files and provenance arrive locally. |
| Databento PCAP route | Databento PCAP is a raw packet-capture market-data route for proprietary exchange feeds and full order book/market depth access. | Useful if Board A needs raw feed reconstruction, but not source/control evidence without acquired files, entitlement, license/provenance, and approval for use as controls. |
| Cboe DataShop legacy CFE VIX route | Cboe DataShop still exposes the legacy CFE VIX futures trades/quotes product for the older VIX window. | Complements the Databento post-2018 route, but remains a DataShop product until exported and staged under the approved root. |
| Prior `044137` CME/Cboe/Databento route recheck | `044137` already counted official CME DataMine, Cboe/CFE DataShop, Databento venues/datasets, and Databento PCAP as source-route context. | This packet is a specificity addendum, not a replacement and not a second acceptance packet. |

## Local Entitlement and Root Check

| Check | Status |
|---|---|
| `databento` CLI | absent |
| `dbn` CLI | absent |
| Python `databento` | absent |
| Python `pyarrow` | absent |
| visible `DATABENTO` / `CME` / `CBOE` / `CFE` env names | absent |
| `/tmp/ict-engine-board-a-r6-owner-export-v1` | absent |
| `/tmp/ict-engine-native-subhour-source-label-intake` | absent |
| `/tmp/ict-engine-source-panel-recency-extension` | absent |
| `/tmp/ict-engine-source-label-equivalence-intake` | present, schema-ready/source-label equivalence only |

## Sources

- Databento CFE announcement: https://databento.com/blog/introducing-cboe-futures-exchange-cfe
- Databento CFE catalog route: https://databento.com/catalog/xcbf/XCBF.PITCH
- Databento PCAP route: https://databento.com/pcaps
- Cboe DataShop CFE VIX futures trades/quotes: https://datashop.cboe.com/cfe-vix-volatility-index-futures-trades-quotes
- Prior local route packet: `docs/experiments/actionable-regime-confidence/runs/20260512T044137-codex-r6-owner-route-web-recheck-after-043901-v1`

## Decision

- The CFE acquisition path is now more specific: `XCBF.PITCH` can target CFE PITCH/MBO-style post-2018 VIX/CFE order-book evidence through Databento when entitlement and API/export tooling are supplied.
- No local Databento entitlement, API key, CLI, Python package, DBN tooling, or verifier-native files are present in this workspace at this readback.
- The three Board A target roots remain absent, and the existing source-label equivalence root remains non-promoting.
- Promotion status remains unchanged: accepted rows added `0`, accepted regime-confidence labels `0`, source/control evidence acquired `false`, new confidence gate `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Use the Databento CFE route only to acquire licensed verifier-native CFE/VIX rows/provenance or to guide operator export requests. Continue the Board A chain only after explicit approval, verifier-native R6 owner/export rows plus source-owned broad normal controls, source-owned R5 recency-extension rows, native sub-hour source-label rows, or genuinely source-owned cross-timeframe `MainRegimeV2` exports unlock a target root.
