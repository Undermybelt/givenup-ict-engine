# Provider Matrix Momentum Downstream v1

Run id: `20260512T130000+0800-codex-113833-provider-momentum-downstream-v1`
Source repair run: `docs/experiments/actionable-regime-confidence/runs/20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1`

## Scope

Downstream readback for the `ProviderCryptoMomentumStateV1` branch from the repaired six-provider 113833 packet.
This consumes only the momentum real-trade wire rows from provider-executed AQ workspaces, in an isolated state dir.

## Provider Matrix

- IBKR: requested=True acquired=True rows=45 local_cache_replay=False
- TradingViewRemix/TVR: requested=True acquired=True rows=720 local_cache_replay=False
- yfinance/YF: requested=True acquired=True rows=983 local_cache_replay=False
- Kraken: requested=True acquired=True rows=721 local_cache_replay=False
- Binance: requested=True acquired=True rows=985 local_cache_replay=False
- Bybit: requested=True acquired=True rows=985 local_cache_replay=False

## Readback

- Merged momentum real-trade rows: `133` from `{'yfinance': 14, 'kraken_public': 23, 'binance_public': 37, 'bybit_public': 34, 'tvr_binance': 25}`.
- Required command exits ok: `True`; exits: `{'00_provider_status': 0, '01_ingest_real_trades': 0, '02_analyze_provider_btc': 0, '03_pre_bayes_status': 0, '04_policy_training_status_before_export': 0, '05_export_structural_path_ranking_target': 0, '06_policy_training_status_after_export': 0, '07_train_catboost': 1, '08_apply_catboost_scores': 1, '11_workflow_structural_bundle': 0, '12_workflow_execution_candidate': 0, '13_workflow_full': 0}`.
- Ingest parsed/applied: `{'command': 'auto-quant-ingest-real-trades', 'content_hash': 'dc62d9ae1304333c', 'dry_run': False, 'feedback_records_inserted': 133, 'force': False, 'ledger_artifact_id': 'auto_quant_real_trades_B2R_PROVIDER_MATRIX_MOMENTUM_113833_20260512T045955.506739000Z', 'ledger_status': 'applied', 'previous_artifact_id': None, 'source': 'auto_quant_real_trades_provider_matrix_momentum_113833', 'symbol': 'B2R_PROVIDER_MATRIX_MOMENTUM_113833', 'trades_applied': 133, 'trades_invalid': 0, 'trades_path': 'docs/experiments/actionable-regime-confidence/runs/20260512T130000+0800-codex-113833-provider-momentum-downstream-v1/derived/provider_matrix_momentum_real_trades.jsonl', 'trades_total': 133}`.
- Structural target rows: `4`; mature_rows: `None`; raw_scored_mature: `None`.
- CatBoost artifact exists: `False`; scores exists: `False`.
- Execution ready/actionable heuristic: `False`; execution gate/status: `None`.

## Decision

- Gate: `provider_matrix_momentum_downstream_fail_closed_no_promotion`.
- This is downstream negative evidence for the same rooted branch, not a production promotion.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
