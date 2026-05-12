# 104703 Exact Branch Path-Ranker Closure v1

Run id: `20260512T113152+0800-codex-104703-exact-branch-path-ranker-closure-v1`

## Scope

This run replays the original 104703 provider-owned BTC EMA/RSI real trades through the downstream state path after the ingest bridge repair. It is isolated under `docs/experiments/actionable-regime-confidence/runs/20260512T113152+0800-codex-104703-exact-branch-path-ranker-closure-v1/state_exact_branch_path_ranker_v1` and does not modify the Current Cursor.

## Evidence

- Source trades: `docs/experiments/actionable-regime-confidence/runs/20260512T104703+0800-codex-board-b-provider-btc-ema-rsi-noncanary-v1/provider_btc_ema_rsi_real_trades_v1.jsonl`
- Ingest applied rows: `42`
- Feedback history rows: `42`
- Exact branch feedback rows: `42` for `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12`
- Structural target rows/history rows: `2` / `44`
- Mature/history mature rows: `1` / `43`
- Raw scored mature: `43/30`
- Production validation: `42/30`
- Observation validation: `42/30`
- Trainer artifact ready: `True` `catboost`
- Runtime enabled/ready: `True` / `True`
- Exact branch target preservation: current and history JSONL rows preserve `regime_profit_branch_path`, `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and `profit_factor`.

## Decision

This repairs the 110221 structural-feedback branch-loss symptom for the 104703 branch by using the preserved real-trade structural feedback rows as the source of truth. It is still not a promotion packet: 104703 remains single-provider/single-window and does not satisfy the six-provider authority gate, selected-history/source-control gate, or full ordered promotion contract. Pre-Bayes and execution-tree readbacks remain fail-closed unless separately promoted by the workflow outputs in `command-output/`.
