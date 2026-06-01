# Board A/B completion audit readback

Use when the user asks whether prior Board A/B GPT/agent work actually achieved the objective, or asks for likely real-world/trading effect.

## Pattern

1. Start from compact current docs, not historical append-only logs:
   - `support/docs/plans/2026-05-12-board-a-regime-state-current.md`
   - `support/docs/plans/2026-05-12-board-b-profit-factor-current.md`
2. Read the repo entry contract first (`AGENT.md`; `CLAUDE.md` may point to it). Honor the rule: current docs are terminal decisions only; start claims live outside repo.
3. Extract the latest explicit completion/audit rows before forming an opinion. Look for:
   - `Board A is not complete` / `Board B is not complete`
   - `objective-completion`, `current-completion`, `completion audit`
   - `update_goal=false`, `not complete`, `not achieved`, `blocked`, `handoff`
4. Open the named `summaries/terminal_decision_summary.md` and checklist artifact (`checks/*.json` or `checks/*.csv`) for the latest audit. Do not summarize from board prose alone.
5. Run a fresh read-only `provider-status --compact` using the available binary (`.local-artifacts/cargo-target/debug/ict-engine` if executable, else `cargo run --quiet -- provider-status --compact`). Treat provider readiness as current context, not as permanent memory.
6. If the question is about practical/trading effect, classify evidence by execution status, not by amount of work:
   - `command exited 0` is not success unless the gate it claims is covered.
   - `branch path preserved` is not promotion.
   - `CatBoost score visible` is not actionable unless execution tree uses it and readiness gates pass.
   - `observe`, `blocked`, `fail_closed`, `pass_neutralized`, low entry-model rows, or `update_goal=false` means not trade-ready.
7. Use decision-row counts only as a quick sanity signal, not as proof. Example Python one-liner can count `Blocked|Handoff|Incubate|Drop|Keep` rows.

## Board-specific readback gates

Board A regime objective is only complete when all are true:
- every regime has calibrated `>=95%` confidence;
- cross-market/cross-period/provider validation is positive;
- real chain ran provider -> Auto-Quant -> Pre-Bayes/filter -> BBN/workflow -> CatBoost/path-ranker -> execution tree;
- named provider families are represented as pass evidence, not only negative/provider-blocked evidence.

Board B profitability objective is only complete when all are true:
- factor is rooted in `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` or an accepted shallower branch key;
- real provider/AQ or native ingest, update feedback, Pre-Bayes/filter, BBN/entry-model readiness, CatBoost/path-ranker, workflow/execution tree all pass for the same rooted branch;
- provider coverage is honest (e.g. label `yf+kraken+ibkr only` if TradingViewRemix is rate-limited/unhealthy);
- execution tree is actionable, not observe/blocked.

## Common conclusion language

- If latest audit says `blocked`, `handoff`, `not complete`, or `update_goal=false`, say the work is real but the objective is not achieved.
- For real-world effect: call it research/observation/candidate incubation unless execution-tree actionability and validation gates pass.
- Do not call recovered/source-backed/diagnostic accepted-95 rows trade-ready unless they are canonically merged and rerun through downstream promotion gates.
