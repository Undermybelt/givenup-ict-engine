# Full-repo candidate-to-live-readiness triage (2026-05-18)

Use when the user asks whether any ict-engine profitability factor is usable in practice, or asks to tune all candidates toward live-ready.

## Durable lessons

- Do not answer from the current run only. Search both repo run artifacts and `/tmp/ict-engine-runs` for candidate evidence: `terminal_metrics.json`, `terminal_decision_summary.md`, `execution_tree_trace.json`, `workflow_snapshot.json`, `ensemble_vote.json`, `auto_quant_agent_material_rank*.json`.
- Rank candidates by the closest hard gate, not raw profit:
  1. `trade_usable=true` / `promotion_allowed=true` / `closed_loop_branch_admission.actionable=true` if any exist.
  2. Mature ranker rows: `raw_scored_mature`, `production_validation`, `observation_validation` >= 30.
  3. Execution tree gate: `execution_gate_status`, `gate_status`, `ready`, `status`.
  4. Cost-stressed AQ profitability: at least 0/1/2/5 bps per side for intraday lanes.
  5. Provider parity: prefer IBKR; TVR/YF/cache are evidence only unless parity is explicit.
- A high-profit AQ row is not live-ready if downstream says `candidate_set_only`, `no_trade`, `observe`, `fail_closed`, or validation rows are insufficient.
- A mature ranker is not live-ready if execution tree blocks it. Example: `IBKR_QQQ_TSMOM_HTF_GATE` had `raw_scored_mature=117/30`, `production_validation=116/30`, `observation_validation=116/30`, `quality_ready=true`, but remained `execution_observe_only`, `actionable=false`, `ready=false`, `fail_closed` due PDA/hybrid/transition guardrail disagreement.
- Thin intraday edges are usually not practical. Example: `IBKR_QQQ_TOD_SLOT_ALPHA_5M_TUNED_CHAIN_R2` kept high win rate but turned weak/negative after realistic cost stress (`net_5bps` negative).
- Strong YF candidates need same-window and provider-parity checks before promotion. Example: SMH Keltner 5m v2 stayed strong on YF same-window (`net_5bps` positive) but IBKR SMH historical timed out and TVR returned only ~216 parseable bars, so parity did not pass.

## Practical workflow

1. Inventory candidates repo-wide, using bounded file search. Avoid broad recursive Python walks over huge run trees; prefer targeted file patterns and parse only decisive JSON/markdown files.
2. Pick the nearest-to-live candidate:
   - Mature-but-blocked: debug execution tree/admission blocker first.
   - Profit-strong-but-immature: add provider parity and validation rows first.
   - Cost-thin: do not keep grinding unless a structural filter improves net 2/5 bps.
3. For each candidate, preserve branch root through every artifact:
   `market/product/symbol/timeframe -> main_regime -> sub_regime -> sub_sub_regime_or_factor -> profit_factor`.
4. Run AQ variants in isolated `/tmp/ict-engine-runs/...` state dirs with `--repo-url <managed-auto-quant-checkout>` when available.
5. Cost stress all low-TF candidates: `net_1bps = profit - trades*0.02`, `net_2bps = profit - trades*0.04`, `net_5bps = profit - trades*0.10` for pct profit and round-trip per-side bps approximation.
6. If provider output JSON is polluted by redaction/control chars but candle objects are visible, regex-extract OHLCV objects into CSV for smoke only; mark as capture-limited and not parity proof.
7. Compare provider windows apples-to-apples: if TVR only returns a short window, run the same calendar window on YF before judging provider divergence.
8. Final claim must state one of:
   - `live-ready`: only if execution/admission + validation + cost + provider gates all pass.
   - `candidate_set_only`: strong candidate but not tradable.
   - `observe/fail_closed`: execution tree rejected.
   - `provider blocked`: data parity blocker, not factor failure.

## Useful artifact examples from the session

- Candidate triage result: `/tmp/ict-engine-runs/20260518T150000+0800-hermes-candidate-tune-inventory-v1/checks/candidate_tune_results.json`
- SMH Keltner v2 parity run: `/tmp/ict-engine-runs/20260518T151500+0800-hermes-smh-keltner-ibkr-parity-v3/summaries/terminal_decision_summary.md`
