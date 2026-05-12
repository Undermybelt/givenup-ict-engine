# Symbol Normalized Path-Ranker Bridge v1

Run id: `20260512T112954+0800-codex-111403-symbol-normalized-path-ranker-bridge-v1`

## Source

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T111403+0800-codex-105014-ingest-bridge-fix-v1`

This run normalizes the BTC pullback real-trade `symbol` field to `B2R_YAHOO_CRYPTO_BTC_PULLBACK_104610` in a copied artifact, then reruns ingest, structural target export, CatBoost path-ranker training/application, trainer registration, runtime enablement, policy status, and workflow status in an isolated copied state.

## Key Readback

- Ingest applied rows: `146`
- Pre-Bayes status: `unknown`
- Target rows/history rows: `2` / `148`
- Mature/history mature rows: `1` / `147`
- Raw scored mature: `147/30`
- Production validation: `146/30`
- Observation validation: `146/30`
- Trainer artifact ready: `True` model `catboost`
- Runtime: enabled `True`, ready `True`, status `enabled_candidate_set_ready`

## Decision

This is a bridge/path-ranker repair diagnostic, not provider authority or Board A promotion evidence. It tests whether the existing 146 BTC pullback feedback observations can become scored mature path-ranker rows once the source symbol and rebuilt exporter are aligned.

Pre-Bayes and execution-tree promotion remain fail-closed unless the command outputs show otherwise; do not call `update_goal` from this run alone.
