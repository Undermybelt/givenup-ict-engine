# R3 Native Sub-hour Contact Route Refresh v1

Run id: `20260512T054833-codex-r3-native-subhour-contact-route-refresh-v1`

Gate result: `r3_native_subhour_contact_route_refresh_v1=current_routes_refreshed_rows_not_acquired_no_promotion`

Board hash before artifact: `6943bcb696337e0f3d36e825dea1e747a55a0caa052724429465cb0f23573116`

## Scope

Bounded contact-route refresh for the R3 native sub-hour blocker after the existing `010401` sendable request package and `044947` live source recheck. This run does not repeat broad Kaggle/Hugging Face source searches. It checks whether the request routes are still reachable and records replacements for stale contact surfaces. It does not send external requests, create labels, download source rows, mutate `/tmp/ict-engine-native-subhour-source-label-intake`, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Route Readback

| Route | URL | HTTP readback | Disposition |
|---|---|---:|---|
| Existing source-label owner dataset | `https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026` | `200` | Keep as source-owner route for asking whether post-`2026-01-30` native 15m/30m labels can be published or approved. |
| Nasdaq Data Link public page | `https://www.nasdaq.com/nasdaq-data-link` | `000` | Local curl blocked or failed; do not treat as row evidence. |
| Nasdaq Data Link old help root | `https://help.data.nasdaq.com/` | `404` | Treat the earlier `nasdaq_data_link_contact` route as stale unless a specific working support page is identified. |
| Nasdaq Data Link / Nasdaq Data official contact | `https://www.nasdaq.net/PublicPages/ContactUs.aspx` | `200` | Use as current replacement contact route for Nasdaq Data Link / Nasdaq Data request dispatch. |
| Nasdaq Indexes contact | `https://indexes.nasdaq.com/contactus` | `200` | Keep as IXIC/index-owner route for native sub-hour label availability or explicit context-only limitation. |
| Yahoo Finance exchanges/data-providers help | `https://help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html` | `200` | More specific Yahoo provenance route than generic Yahoo Finance help; still provider metadata, not labels. |

## Decision

The R3 request package can be sharpened with two route updates:

- Replace the stale Nasdaq Data Link `/contact` style route with the working `nasdaq.net` public contact route for Nasdaq Data / Nasdaq Data Link dispatch.
- Prefer the Yahoo exchanges/data-providers help page over the generic Yahoo Finance help surface when asking about provider provenance; this still cannot close R3 without source-native labels.

No source-owned native sub-hour `MainRegimeV2` rows were found or acquired. Required target root `/tmp/ict-engine-native-subhour-source-label-intake` remains absent, and the R6/R5 target roots remain absent. Promotion remains blocked: accepted rows added `0`, source/control evidence acquired false, target root mutated false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Use the refreshed routes only to send or satisfy the existing R3 native sub-hour request package. Continue Board A promotion only after source-owned AAPL/IXIC native 15m/30m labels plus provenance are placed under the required intake root, or another approved source/control root unlocks; then rerun direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
