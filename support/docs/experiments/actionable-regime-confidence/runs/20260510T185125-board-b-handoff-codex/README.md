# Board B Handoff: SessionLiquidityCoreViable

Run ID: `20260510T185125-board-b-handoff-codex`

Purpose: consume Board A's accepted 95% `SessionLiquidityCoreViable` packet through the downstream `ict-engine` chain without treating it as a standalone trade signal.

## Inputs

- Accepted packet: `docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity/session-liquidity/session_liquidity_regime_probe_report.json`
- Consumer bundle: `regime-sidecar/regime_consumer_bundle.json`
- Decision sidecar: `regime-sidecar/regime_high_confidence_decision.json`

## Runtime Path

The first `analyze-live` attempt used `--futures-symbol QQQ` and failed because Yahoo mapped it to invalid `QQQ=F`.

The corrected run used:

```bash
./target/debug/ict-engine analyze-live \
  --symbol QQQ \
  --futures-symbol NQ=F \
  --spot-symbol QQQ \
  --options-symbol QQQ \
  --futures-backend yfinance \
  --aux-backend yfinance \
  --state-dir docs/experiments/actionable-regime-confidence/runs/20260510T185125-board-b-handoff-codex/ict-engine/state \
  --output-format json \
  --regime-consumer-bundle docs/experiments/actionable-regime-confidence/runs/20260510T185125-board-b-handoff-codex/regime-sidecar/regime_consumer_bundle.json \
  --regime-consumer-bundle-strict \
  --apply-regime-bundle-bbn-soft-evidence
```

## Result

- Regime bundle loaded under strict mode.
- Accepted label: `SessionLiquidityCoreViable`.
- Confidence lane: 95%.
- Test Wilson95: `0.9899396497369397`.
- `trade_usable=false`, because this is a liquidity/session guardrail, not a directional release rule.
- Pre-Bayes: `pass_neutralized`.
- BBN soft evidence: skipped with `no_supported_label`.
- Execution tree: `observe / transition_guardrail / guarded`.
- Path ranker: `unknown / unknown / not_ready`; score not used by execution tree.
- Policy training: 0 matched rows for both CISD RB and Breaker RB; CatBoost/path-ranker target export not ready.
- Next blocker: `user_selected_historical_data_missing` before deferred QQQ factor-research.

CatBoost availability was verified separately with offline `uv --with catboost` and a minimal fit using CatBoost `1.2.10`; dependency absence is not the blocker for this handoff.

