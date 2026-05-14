# 104703 Provider-Data Pre-Bayes Path-Ranker Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T112740+0800-codex-104703-provider-data-prebayes-pathranker-readback-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T104703+0800-codex-board-b-provider-btc-ema-rsi-noncanary-v1`

Path-ranker source root: `docs/experiments/actionable-regime-confidence/runs/20260512T112900+0800-codex-104703-exact-branch-structural-feedback-closure-v1`

Symbol: `B2R_PROVIDER_BTC_EMA_RSI_104703`

## Result

Gate: `104703_provider_data_prebayes_pathranker_readback_v1=pre_bayes_populated_catboost_pathranker_ready_but_execution_blocked_no_promotion`

This run copied the path-ranker-ready `104703` branch state from `112900`, converted the provider-owned BTC/USDT 1d/4h/1h feather files to `ict-engine analyze` JSON candles, ran `analyze`, then reran Pre-Bayes, policy/path-ranker, structural bundle, execution-candidate, and full workflow readbacks.

## Evidence

- Core commands exited `0`: `True`.
- Provider data rows: 1d `42`, 4h `247`, 1h `985` from `2026-04-01T00:00:00Z` through `2026-05-12T00:00:00Z` on the 1d frame.
- Pre-Bayes populated: gate `pass_neutralized`, policy `318900600c5e8cf2`, canonical structural regime `range`, confidence `0.5345590139527494`.
- Market-state filter: `RangeConsolidation` / `WideRange`; MTF bias `bullish` with alignment `0.9967`.
- CatBoost path-ranker: runtime `enabled_candidate_set_ready`, source `candidate_set`, model `catboost` / `external_model`.
- Path-ranker validation: raw scored mature `86/30`, production validation `85/30`, observation validation `43/30`, calibration `evaluated`.
- Execution candidate preserved path `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12` with raw score `0.9009131229620996` and Pre-Bayes gate `pass_neutralized`.

## Decision

This is a real improvement over `112900`: Pre-Bayes is no longer empty, and path-ranker validation remains above floor. It still cannot promote because execution remains blocked/observe: candidate status `execution_blocked`, execution gate `execution_blocked`, readiness `0.3363756308524155`, ready `False`, actionable `False`, review `observe`.

The full workflow also remains non-promoting because selected-history/source-control gates are closed and the same-root six-provider AQ matrix is still absent. Accepted rows added `0`; mature rooted branch observations promoted `0`; source/control evidence acquired `false`; explicit selected-history `false`; canonical merge `false`; same-root six-provider AQ matrix `false`; downstream promotion `false`; strict full objective `false`; trade usable `false`; promotion allowed `false`; `update_goal=false`.

## Notes

The first export command used the stale `--output-format` flag and exited `2`. A corrected `04b_export_structural_path_ranking_target_corrected` command exited `0`, so this is recorded as a command-shape correction, not a model/runtime blocker.

## Next

Do not promote from this readback. The next useful slice is to resolve the explicit selected-history/source-control gate and the execution readiness block (`readiness < 0.45`) on this same rooted branch, or build a same-root six-provider AQ packet that includes IBKR, TVR, YF, Kraken, Binance, and Bybit before repeating the ordered downstream chain.
