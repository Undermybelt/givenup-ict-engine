# Provider Chain Intake Gap Recheck v1

- Decision: `provider_chain_intake_gap_recheck_v1=real_chain_ran_r6_schema_ready_unscored_remaining_intakes_blocked`
- Scope: real provider readback plus Auto-Quant and ict-engine chain readback; no runtime code changes and no raw market rows committed.
- Board hash before writeback: `f6b8e2deb8312b949f4866eb649d8f9dafa1da2b8bbf7800ba6af6b3d31d1427`

## Provider Fetches

| Provider | Rows | First | Last | Raw Location |
|---|---:|---|---|---|
| `yfinance_QQQ_1h` | 3369 | `2024-06-03 13:30:00+00:00` | `2026-05-08 20:00:00+00:00` | `/tmp/ict-engine-board-a-20260511T204948-provider-chain-intake-gap-recheck-v1/provider_raw/yahoo_QQQ_1h.csv` |
| `tradingview_mcp_QQQ_1h` | 140 | `2026-04-13T13:30:00Z` | `2026-05-08T19:30:00Z` | `/tmp/ict-engine-board-a-20260511T204948-provider-chain-intake-gap-recheck-v1/provider_raw/tradingview_mcp_QQQ_1h.json` |
| `ibkr_QQQ_1h_1M` | 325 | `2026-04-13T08:00:00+00:00` | `2026-05-11T12:00:00+00:00` | `/tmp/ict-engine-board-a-20260511T204948-provider-chain-intake-gap-recheck-v1/provider_raw/ibkr_QQQ_1h_1M.csv` |
| `kraken_XBTUSD_1h` | 721 | `2026-04-11 12:00:00+00:00` | `2026-05-11 12:00:00+00:00` | `/tmp/ict-engine-board-a-20260511T204948-provider-chain-intake-gap-recheck-v1/provider_raw/kraken_XBTUSD_1h.csv` |

## Auto-Quant

- Strategy: `TomacNQ_RegimeTrendPullback`
- Trades: `3925`; win rate: `47.4904`; Sharpe: `-7.598`; robust Sharpe: `-7.598`.
- Log: `/tmp/ict-engine-board-a-20260511T204948-provider-chain-intake-gap-recheck-v1/autoquant_run.log`

## ict-engine Chain

- Analyze: direction `Bull`, decision `Observe only`, execution gate `observe`.
- Pre-Bayes/BBN: gate `pass_neutralized`, active regime `trend`, confidence `0.5822867835012198`.
- CatBoost/path-ranker status: ready `False`; policy summary `entry-model training modules mixed: ready=[] pending=[cisd_rb_long_v1,breaker_rb_long_v1] | structural path ranking target export missing runtime_selection=disabled runtime_source=none runtime_matches=0`.
- Execution tree: candidate status `no_trade`, review `observe`, actionable `False`.

## Direct Manipulation Verifier

- Verifier status: `schema_ready_unscored`.
- Positive rows: `2`; matched negative rows: `2`; matched groups: `1`.
- Next verifier action: `run chronological and heldout-symbol/venue Wilson95 calibration gate`.

## Intake Gate

- Ready intake roots: `1/4`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

| Requirements | Root | Ready | Missing |
|---|---|---|---|
| `R2;R4` | `/tmp/ict-engine-source-label-equivalence-intake` | `false` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `R3` | `/tmp/ict-engine-native-subhour-source-label-intake` | `false` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `R5` | `/tmp/ict-engine-source-panel-recency-extension` | `false` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `R6` | `/tmp/ict-engine-direct-manipulation-row-intake` | `true` | `` |

## Decision

The providers and local chain are operable, including TradingView MCP, yfinance, IBKR through the local gateway, Kraken, Auto-Quant, Pre-Bayes/BBN readback, policy/CatBoost status, structural path ranking export, and execution-candidate readback. R6 direct-manipulation intake is now schema-ready, but it is unscored and not a 95% confidence gate; R2/R3/R4/R5 source-owned or owner-approved intake files are still absent.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204948-codex-provider-chain-intake-gap-recheck-v1/provider-chain-intake-gap-recheck/provider_chain_intake_gap_recheck_v1.json`
- Provider CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204948-codex-provider-chain-intake-gap-recheck-v1/provider-chain-intake-gap-recheck/provider_chain_intake_gap_recheck_v1_providers.csv`
- Intake CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204948-codex-provider-chain-intake-gap-recheck-v1/provider-chain-intake-gap-recheck/provider_chain_intake_gap_recheck_v1_intake_roots.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204948-codex-provider-chain-intake-gap-recheck-v1/checks/provider_chain_intake_gap_recheck_v1_assertions.out`
