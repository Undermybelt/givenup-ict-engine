# Current Objective Audit After 033625 v1

Run id: `20260512T034055-codex-current-objective-audit-after-033625-v1`

Gate result: `current_objective_audit_after_033625_v1=not_complete_autoquant_oracle_succeeded_diagnostic_only_source_control_downstream_blocked`

## Objective Restatement

Board A is complete only if every active regime has calibrated confidence >=95%, its own qualifying condition, cross-market/cycle/timeframe/provider validation, and a real local chain in order: provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree.

## Prompt-to-Artifact Checklist

- `pass` Use the named board as the live contract without disrupting concurrent work: d4bdd2ad485f47bedb3f3ca41a9ea6d00883ff3dcd16301a0a9986be9806d89c  docs/plans/2026-05-10-actionable-regime-confidence-todo.md
- `blocked` Every active regime has calibrated confidence >=95%: live_verifier_status=schema_ready_unscored
- `blocked` Each regime has its own qualifying conditions: accepted_rows_added=0
- `blocked` Cross-market/cycle/timeframe validation passes: {'/tmp/ict-engine-board-a-r6-owner-export-v1': False, '/tmp/ict-engine-native-subhour-source-label-intake': False, '/tmp/ict-engine-source-panel-recency-extension': False, '/private/tmp/ict-engine-direct-manipulation-row-intake': True, '/private/tmp/ict-engine-source-label-equivalence-intake': True, '/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid': True}
- `partial` Operate providers: IBKR, TradingViewRemix/TradingView, yfinance, Kraken: yfinance=True kraken_cli=True ibkr=configured_runtime_unhealthy tradingview_mcp=configured_runtime_unhealthy
- `pass` Operate AutoQuant locally: 3 backtests succeeded with absolute threaded-resolver shim
- `blocked` Run filter / Pre-Bayes readback: latest_gate_status=None
- `blocked` Run BBN / policy-training readback: entry-model training modules mixed: ready=[] pending=[cisd_rb_long_v1,breaker_rb_long_v1] | structural path ranking target export missing runtime_selection=disabled runtime_source=none runtime_matches=0
- `blocked` Run CatBoost / path-ranking readback: structural path ranking target export missing runtime_selection=disabled runtime_source=none runtime_matches=0
- `blocked` Run execution-tree / workflow readback: no workflow phase snapshots available
- `pass` Do not promote proxy/runtime/local-cache evidence into Board A acceptance: owner_export=False approval_present=False canonical_merge=False

## AutoQuant Diagnostic Result

- Plain `uv --directory ... run run.py` failed through `aiodns` / Binance market loading.
- Absolute threaded-resolver shim run exited `0`: `3` backtests succeeded and `0` failed.
- Best diagnostic strategy by Sharpe in this run: `VolBreakoutSized` with Sharpe `1.3390`, total profit `25.0200%`, trade count `1221`, win rate `32.8419%`, profit factor `1.4751`, but `min_position_size=FAIL`.
- This is AutoQuant runtime diagnostics only. It is not regime-confidence calibration and not Board A acceptance.

## Source / Control Gate

- Live sidecar verifier: `schema_ready_unscored`, positives `73`, matched negatives `73`, groups `70`.
- Required owner-export verifier: exit `2`, status `blocked`, reason `missing_required_files`.
- Required owner-export, R3 native-subhour, and R5 recency-extension roots remain absent.
- Approval package remains non-approving; canonical merge and downstream rerun are not allowed.

## Downstream Readback

- Pre-Bayes latest gate: `None`.
- Policy/CatBoost/path-ranking: `entry-model training modules mixed: ready=[] pending=[cisd_rb_long_v1,breaker_rb_long_v1] | structural path ranking target export missing runtime_selection=disabled runtime_source=none runtime_matches=0`.
- Workflow/execution-tree blocking truth: `insufficient_state` / `no workflow phase snapshots available`.

## Decision

- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Preserve the Current Cursor: acquire verifier-native R6 owner/export rows or explicit FLIP-control approval before canonical merge and downstream promotion. AutoQuant oracle success is diagnostic only until source/control gates unlock.
