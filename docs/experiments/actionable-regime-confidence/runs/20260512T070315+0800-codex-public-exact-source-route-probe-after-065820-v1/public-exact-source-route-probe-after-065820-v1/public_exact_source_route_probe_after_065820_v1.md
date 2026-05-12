# Public Exact Source Route Probe After 065820 v1

Run id: `20260512T070315+0800-codex-public-exact-source-route-probe-after-065820-v1`

Gate result: `public_exact_source_route_probe_after_065820_v1=public_context_found_no_verifier_native_rows_no_unlock`

## Scope

Readback of the public exact-source route probe after `065820` rejected the current R5/R3 public candidates. This packet records existing command outputs in this run root. It does not download additional raw data, mutate R3/R5/R6 target roots, approve public dashboard/article sources, run canonical merge, run downstream promotion, make a trade claim, or call `update_goal`.

## Commands / Outputs Read

- Search query list: `command-output/web_search_queries_v1.txt`
- CFTC Oystacher press release `7264-15`: `command-output/curl_https___www_cftc_gov_PressRoom_PressReleases_7264_15.body`
- CFTC Oystacher press release `7504-16`: `command-output/curl_https___www_cftc_gov_PressRoom_PressReleases_7504_16.body`
- CFTC complaint PDF: `/tmp/ict-engine-board-a-public-exact-source-route-probe-after-065820-v1/enfigorcomplnt101915.pdf`
- Complaint PDF SHA-256: `6a2a951e3c02285cb1df085e314c7ae2a2a0c089f283998641ea66fce5ce8591`
- Hidden-regime PyPI summary: `command-output/hidden_regime_pypi_summary.json`

## Decision

| Candidate | Observed | Board A Decision |
|---|---|---|
| CFTC press release `7264-15` | Public page title confirms Oystacher/3 Red spoofing allegations across E-mini S&P 500, Copper, Crude Oil, Natural Gas, and VIX futures. | Useful public route/provenance context only. It is not a verifier-native row export and not source-owned normal controls. |
| CFTC press release `7504-16` | Public page title confirms federal court penalty/order context for Oystacher/3Red spoofing. | Useful public route/provenance context only. It is not source-owned order-lifecycle rows or accepted controls. |
| CFTC complaint PDF | Downloaded PDF is present and hashed, but `pdftotext` and `pdfinfo` were unavailable in this run, and no row-level parsed source/control packet was produced. | Do not promote. A public complaint PDF is not `/tmp/ict-engine-board-a-r6-owner-export-v1` owner/export rows with valid controls. |
| `hidden-regime` package | PyPI package `hidden-regime` version `2.0.2`, summary says market regime detection with HMM/Bayesian uncertainty, uploaded `2025-11-24`. | Library/tooling context only. It is not source-owned `MainRegimeV2` labels, not R5 recency rows, and not R6 controls. |

## Gate

- R6 owner/export unlock: `false`
- R5 recency unlock: `false`
- R3 native-subhour unlock: `false`
- Valid required-root unlock: `false`
- Source/control evidence acquired: `false`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant promotion, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
