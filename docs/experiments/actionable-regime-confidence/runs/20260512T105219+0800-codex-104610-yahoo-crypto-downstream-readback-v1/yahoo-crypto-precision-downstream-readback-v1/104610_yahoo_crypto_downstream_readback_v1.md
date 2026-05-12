# 104610 Yahoo Crypto Downstream Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T105219+0800-codex-104610-yahoo-crypto-downstream-readback-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T104610+0800-codex-board-b-yahoo-crypto-precision-fix-aq-v1`

This is a non-counting downstream readback for the already-counted `104610` Yahoo crypto precision-fix AQ root. It does not approve selected history, source/control evidence, canonical intake mutation, selected-data AutoQuant promotion, downstream promotion, live trade use, completion, or `update_goal`.

## Inputs

- Strategy library: `104610_yahoo_crypto_precision_strategy_library_v1.json`
- Combined real trades: `104610_yahoo_crypto_precision_real_trades_combined_v1.jsonl`
- Combined real-trade rows: `1326`
- Imported strategies: `ProviderCryptoMomentumStateV1`, `ProviderCryptoPullbackRevertV1`

## Source AQ Metrics

- `ProviderCryptoMomentumStateV1`: `944` trades, `-57.41%` total profit, Sharpe `-3.8948`, win rate `30.1907%`, profit factor `0.6793`, max drawdown `-60.0640%`.
- `ProviderCryptoPullbackRevertV1`: `382` trades, `-9.64%` total profit, Sharpe `-0.5777`, win rate `42.4084%`, profit factor `0.8775`, max drawdown `-10.0987%`.
- The BTC/USDT pullback subslice was weakly positive (`146` trades, `+2.65%`, Sharpe `0.1930`, profit factor `1.1218`), but the aggregate strategy and cross-pair panel remain negative.

## Ordered Chain Readback

- `auto-quant-results-import` exited `0`: `n_ok=2`, `n_error=0`, `n_total_strategies=2`.
- `auto-quant-prior-init` exited `0`: both strategies applied; final CPT probabilities were `[0.4216979023486318, 3.792286145227321e-9, 0.5783020938590822]`.
- `auto-quant-ingest-real-trades` exited `0`: `trades_applied=1326`, `trades_invalid=0`, `feedback_records_inserted=1326`.
- `pre-bayes-status` exited `0` but remained empty: no latest policy, bridge, soft evidence, filtered assignments, or canonical structural regime.
- `policy-training-status` after export exited `0`: entry models matched `0` rows; structural path target rows `1`, history rows `1`, mature rows `0`, raw scored mature `0/30`, production validation `0/30`, observation validation `0/30`, calibration `not_fitted`, trainer artifact `missing`, runtime selection `disabled`.
- `workflow-status` exited `0` but remained fail-closed: selected path `path:scenario:B2R_YAHOO_CRYPTO_PRECISION_104610:bootstrap:no_workflow_state:bootstrap_collect_inputs:primary`, execution candidate `ready=false`, `actionable=false`, `review_status=observe`, and `closed_loop_branch_admission.status=fail_closed`.

## Decision

Gate: `104610_yahoo_crypto_downstream_readback_v1=real_trades_ingested_downstream_fail_closed_no_promotion`.

This readback proves the ordered ict-engine surfaces can ingest the mature non-canary AQ rows, but it does not make the root promotable. The AQ panel is aggregate-negative, the BTC-only positive subslice is not cross-pair validation, Pre-Bayes remains empty, CatBoost/path-ranking has no mature rows, execution stays bootstrap/observe, and the later A/B AQ provider authority gate still requires provider-matrix provenance that this local replay does not satisfy.

Net Board A effect remains unchanged: accepted rows added `0`, mature rooted branch observations promoted `0`, source/control evidence acquired `false`, explicit selected-history `false`, canonical merge `false`, selected-data AutoQuant promotion `false`, downstream promotion `false`, strict full objective `false`, trade usable `false`, promotion allowed `false`, and `update_goal=false`.

## Next

Do not promote or rerun this exact `104610` downstream shape. The next useful slice is a provider-matrix-backed AQ packet for the same rooted branch, explicit selected-history/source-control unlock, or a different branch-specific recipe that can survive cross-pair/timeframe controls before the ordered downstream readback.
