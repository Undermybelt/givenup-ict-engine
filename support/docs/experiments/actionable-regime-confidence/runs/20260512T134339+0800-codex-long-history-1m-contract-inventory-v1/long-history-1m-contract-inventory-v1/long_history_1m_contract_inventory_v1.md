# Long-History 1m Contract Inventory v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T134339+0800-codex-long-history-1m-contract-inventory-v1`

## Purpose

This packet is a direction correction after the user rejected short-window validation. It is not a regime acceptance packet, not a profitability packet, and not an execution promotion. It records the local long-history 1m data now found and defines the evidence contract required before Board A can claim any `>=95%` regime confidence.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Stop treating a few days/weeks as enough | This report marks short-window ETH/provider probes as support-only unless they are embedded in a long-history validation | pass |
| Locate local 1m long-history data first | `local_1m_inventory.csv` inventories ES, NQ, YM, EUR, and GC/XAU futures files | pass |
| Preserve six-provider requirement | Contract below keeps IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit as mandatory provider-context/provenance gates | pass as contract, not yet satisfied |
| Preserve chain order | Contract requires Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree | pass as contract, not yet executed on long data |
| Avoid acceptance from local replay only | Local long-history data is primary validation substrate, but selected-history/local replay alone remains support/debug unless provider/context gates also pass | pass |
| Do not call completion | `update_goal=false`; accepted contexts remain `0` | pass |

## Local 1m Inventory

Primary raw 1m files found under `/Users/thrill3r/Downloads/Tomac/`:

| Market | Source | Rows incl. header | First row | Last row | Role |
|---|---|---:|---|---|---|
| ES futures | Databento GLBX MDP3 local CSV | 8,433,934 | 2010-06-06T22:00:00Z | 2026-04-03T13:14:00Z | primary long-history candidate |
| NQ futures raw | Databento GLBX MDP3 local CSV | 7,059,923 | 2010-06-06T22:00:00Z | 2026-04-03T13:14:00Z | primary long-history candidate |
| NQ futures adjusted | local continuous shifted CSV | 5,302,714 | 2011-01-02 23:00:00+00:00 | 2025-12-31 21:59:00+00:00 | support/debug unless provenance accepted |
| YM futures | Databento GLBX MDP3 local CSV | 5,991,017 | 2011-01-02T23:00:00Z | 2025-12-31T21:59:00Z | cross-instrument validation |
| EUR futures | Databento GLBX MDP3 local CSV | 5,446,508 | 2015-01-01T23:00:00Z | 2025-12-31T21:59:00Z | FX futures cross-market validation |
| GC futures | Databento GLBX MDP3 local CSV | 5,333,533 | 2021-01-06T00:00:00Z | 2026-01-05T23:59:00Z | shorter metals validation |

Cleaned multi-timeframe 1m manifest already exists under `/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/`:

| Market | Raw rows | Continuous 1m candles | Selected window |
|---|---:|---:|---|
| ES | 8,433,933 | 299,107 | 2012-04-23T13:38:00Z to 2025-08-04T12:10:00Z |
| NQ | 7,059,922 | 301,577 | 2012-07-06T12:46:00Z to 2023-10-26T16:19:00Z |
| EUR | 5,446,507 | 200,224 | 2020-06-29T15:17:00Z to 2023-12-18T13:34:00Z |
| YM | 5,991,016 | 86,113 | 2014-02-14T17:57:00Z to 2025-09-18T20:59:00Z |
| XAU | 5,333,532 | 125,051 | 2021-07-12T00:02:00Z to 2023-06-09T17:28:00Z |

The main Auto-Quant `user_data/data` directory currently has no native `1m` file; it has `5m`, `15m`, `1h`, `4h`, and `1d` files. That means the next valid Auto-Quant slice must explicitly import or stage the 1m futures data rather than reusing current AQ cache as if it already met the long-history standard.

## Revised Board A Evidence Contract

No Board A acceptance may be claimed from windows like `572` hourly rows or `26` daily bars. Those are diagnostics only.

Minimum acceptance standard for each main regime:

- Data horizon: 1m primary validation over approximately 15 years where local history supports it. ES/NQ raw futures qualify as the current primary substrate; shorter markets such as GC/XAU are cross-market support only unless their shorter horizon is explicitly accepted as a separate validation tier.
- Splits: chronological train/validation/test plus walk-forward slices, including pre-2020, 2020-2022, 2023-2024, and 2025-2026 where data exists.
- Per-regime threshold: each main regime must have its own qualifying condition and calibrated posterior/path lower bound `>=0.95`; one accepted regime cannot lend support to another.
- Cross-market/timeframe: validate on at least ES/NQ plus one non-index family where available; rerun 1m base with aggregated 5m/15m/1h/4h/1d contexts.
- Provider context: IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit must be recorded in a provider matrix for the feasible overlapping windows. If a provider cannot supply the full long-history 1m horizon, that limitation is a fail-closed provider-context gap, not an excuse to promote short-window evidence.
- Ordered runtime chain: Auto-Quant candidate generation/backtest must feed filter/Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree admission in order. Direct Auto-Quant metrics cannot skip the intermediate layers.
- Promotion blockers: selected-history/local replay, short provider overlaps, CatBoost numeric floors, or observe-only execution are insufficient. Acceptance requires non-observe gate, calibrated confidence/lower bound, mature CatBoost/path rows, and execution readiness/actionability.

## Current Decision

The active direction is changed. Existing short-window six-provider ETH evidence remains useful as plumbing and contract-negative evidence, but it is not a basis for Board A acceptance. The next execution slice should stage the long 1m futures data into an isolated Auto-Quant/ict-engine run root and run the chain on ES/NQ first, with provider-context matrix recorded separately.

Gate:

- `support_once:long_history_1m_contract_inventory_v1`
- `evidence_class:direction_correction_and_data_inventory`
- `pass:local_1m_long_history_found`
- `pass:es_nq_raw_1m_2010_to_2026_available`
- `pass:cleaned_mtf_1m_json_manifest_available`
- `fail_closed:auto_quant_main_cache_has_no_1m_native_files`
- `fail_closed:provider_context_matrix_not_yet_long_history_validated`
- `fail_closed:no_auto_quant_long_1m_backtest_yet`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_long_1m_chain_yet`
- `accepted_95_contexts=0`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Evidence Files

- Raw 1m inventory: `long-history-1m-contract-inventory-v1/local_1m_inventory.csv`
- Cleaned 1m manifest summary: `long-history-1m-contract-inventory-v1/cleaned_mtf_1m_manifest_summary.csv`
- Auto-Quant main data listing: `command-output/auto_quant_data_files.out`
- Exit checks: `checks/`

## Next

Stage an isolated ES/NQ long-history 1m run that starts from the local Tomac data and produces a real Auto-Quant candidate packet. Only after that packet exists should the chain proceed to filter/Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree admission. Keep all short-window provider probes as support/debug until they are tied back into this long-history evidence contract.
