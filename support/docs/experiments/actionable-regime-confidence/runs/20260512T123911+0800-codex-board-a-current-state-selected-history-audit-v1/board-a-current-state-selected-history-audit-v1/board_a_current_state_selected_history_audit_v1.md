# Board A Current State Selected-History Audit v1

Run id: `20260512T123911+0800-codex-board-a-current-state-selected-history-audit-v1`
Board SHA-256 at artifact time: `16fb0cd3800fca54405b8d617abe8be655f29fc7444b76f715f9e5092068b8aa`

## Objective Readback
- Required outcome: every regime at `>=95%` confidence, validated across other markets/instruments and periods/timeframes, through real Auto-Quant -> ict-engine -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree evidence.
- Current result: strict objective is not achieved.

## Latest Evidence
- Provider-node cross-context gate `20260512T122933+0800-codex-115700-provider-evidence-node-cross-context-gate-v1` remains fail-closed: max BBN probability `0.747688`, instruments `['BTC']`, timeframes `['1h']`, accepted feature gates `0`.
- Selected-history native preflight `20260512T123211+0800-codex-115700-selected-history-preflight-v1` ran `3` data paths; all command exits were zero: `True`, but ready/actionable count is `0`.
- Selected-history Auto-Quant `20260512T123227+0800-codex-115700-selected-history-btc-alias-aq-v1` prepared data with status `prepared` and `data_ready=True`; patched `run_tomac` exit `0` produced total trades `0` across `3` strategies.
- Provider-node split validation `20260512T123233+0800-codex-122351-provider-node-split-validation-v1` best internal candidate is `provider_rv_median_24h`, still candidate-only.

## Decision
- Gate: `board_a_current_state_selected_history_audit_v1=strict_goal_not_achieved_no_update_goal`.
- Do not mutate BBN likelihoods/CPDs from this packet.
- Do not promote execution or trade use.
- Do not call `update_goal`.

## Next
- Let active selected-history pairmap/run_tomac jobs finish, then only register their settled output if it adds non-duplicate evidence.
- The remaining high-value gap is still non-BTC, non-1h/cross-period evidence plus a pre-trade BBN node that can lift a specific regime toward `>=95%` and survive execution-readiness gates.
