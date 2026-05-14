# R3/R5 Current Source Label Search v1

Run id: `20260512T055116-codex-r3-r5-current-source-label-search-v1`

Gate result: `r3_r5_current_source_label_search_v1=no_exact_native_subhour_or_mainregime_source_rows_no_promotion`

Board hash before artifact: `879d26294e01cd2e829858fef422df671249d41032f1397a51507ad60a1e51cc`

## Scope

Bounded current source-label search after `055011` and the corrected `055129` provider/Auto-Quant readback. This run checks whether current Kaggle or Hugging Face search surfaces expose exact R3 native sub-hour labels or R5/MainRegimeV2 source-owned rows. It does not send external requests, download the large raw Bybit package, create labels, mutate `/tmp/ict-engine-native-subhour-source-label-intake`, mutate `/tmp/ict-engine-source-panel-recency-extension`, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Commands

Kaggle searches all exited `0`:

- `Bull Bear Sideways Crisis market regime labels`
- `AAPL 15m regime label`
- `IXIC 15m regime label`
- `NQ futures 15m regime label`
- `crypto market regime labels 15m`
- `market regime labels intraday`

Hugging Face API searches all exited `0`:

- `AAPL 15m regime label`
- `IXIC 15m regime label`
- `Bull Bear Sideways Crisis market regime labels`
- `market regime labels intraday`

The Bybit candidate file listing also exited `0`:

- `thisathdamiru/bybit-multi-crypto-historical-data-2020-2026`

Raw command outputs are under `command-output/`.

## Readback

| Surface | Result | Decision |
|---|---|---|
| Kaggle exact `AAPL 15m regime label` | `No datasets found` | No R3 unlock. |
| Kaggle exact `IXIC 15m regime label` | `No datasets found` | No R3 unlock. |
| Kaggle exact `NQ futures 15m regime label` | `No datasets found` | No R3 unlock. |
| Kaggle exact `Bull Bear Sideways Crisis market regime labels` | `No datasets found` | No R5/MainRegimeV2 unlock. |
| Kaggle broad intraday/crypto regime searches | Found `thisathdamiru/bybit-multi-crypto-historical-data-2020-2026`. | Raw 5m OHLCV files only from listing; not source-owned regime labels. |
| Hugging Face searches | Empty arrays for all four queries. | No R3/R5 unlock. |

Bybit file listing showed raw 5m files such as:

- `BYBIT_0GUSDT_SPOT_5m.csv`
- `BYBIT_AAPLXUSDT_SPOT_5m.csv`
- `BYBIT_ADAUSDT_SPOT_5m.csv`

These are raw market-data files, not source-owned `MainRegimeV2` labels, not AAPL/IXIC native sub-hour labels, and not provenance-approved R5 recency rows.

## Decision

No exact source-label package was found. Required roots remain absent:

- `/tmp/ict-engine-board-a-r6-owner-export-v1`
- `/tmp/ict-engine-native-subhour-source-label-intake`
- `/tmp/ict-engine-source-panel-recency-extension`

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Continue only after explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root. Then rerun direct verifier, split calibration, canonical merge, providers, Auto-Quant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
