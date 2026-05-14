# Provider-Owned AQ Prepare Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1`

Mode: `provider_prepare_readback_only`

## Scope

This is an additive readback after the provider-owned acquisition packet. It confirms that the successful provider CSV sidecar was pre-seeded into the isolated Auto-Quant workspace. It does not run `run_tomac.py`, does not run selected-data AutoQuant promotion, does not advance Pre-Bayes/BBN/CatBoost/execution-tree promotion, does not edit Current Cursor, and does not call `update_goal`.

## Commands

- `10_auto_quant_prepare_provider_yf`: exit `0`
- `11_auto_quant_status_after_prepare`: exit `0`

## Readback

`ict-engine auto-quant-prepare` finished successfully for:

`docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/state_provider_owned_aq_v1`

`auto-quant-status` now reports:

- status: `dependency_ready_data_ready`
- healthy: `true`
- dependency healthy: `true`
- data ready: `true`
- profile note: `auto_quant_profile=synthetic_ohlcv`
- next command: `uv run --with ta-lib docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/state_provider_owned_aq_v1/.deps/auto-quant/run_tomac.py`

Prepared Auto-Quant data files:

- `B2R_NQ_PROVIDER_100419_USD-1h.feather`
- `B2R_NQ_PROVIDER_100419_USD-4h.feather`
- `B2R_NQ_PROVIDER_100419_USD-1d.feather`

The successful provider-owned source for this pre-seed is still the Yahoo `NQ=F` hourly CSV from the parent acquisition packet. Kraken/Binance/Bybit BTC CSVs remain cross-provider sidecars and were not consumed into this NQ Auto-Quant state in this readback.

## Gate

- `pass:provider_owned_yahoo_nq_preseeded_into_autoquant`
- `pass:auto_quant_status_dependency_ready_data_ready`
- `fail_closed:no_autoquant_run_tomac_yet`
- `fail_closed:no_nonzero_mature_rooted_branch_observations_yet`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_promotion_rerun`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Run the recommended provider-preseeded Auto-Quant command only when there is no competing heavy factor-training run:

`uv run --with ta-lib docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/state_provider_owned_aq_v1/.deps/auto-quant/run_tomac.py`

Advance to Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree only if that provider-preseeded run emits nonzero mature rooted branch observations.
