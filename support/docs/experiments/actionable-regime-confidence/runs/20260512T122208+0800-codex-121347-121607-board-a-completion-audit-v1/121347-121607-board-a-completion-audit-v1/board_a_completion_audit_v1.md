# Board A Completion Audit v1

Run id: `20260512T122208+0800-codex-121347-121607-board-a-completion-audit-v1`
Source enriched run: `20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`
Source feedback run: `20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1`

## Objective
Every active regime needs calibrated >=95% confidence, must survive other market/instrument and other timeframe/cycle validation, and must be proven through the local Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree chain before any result/completion claim.

## Current Evidence
- Enriched rows audited: `237`.
- Providers: `['binance_public', 'bybit_public', 'ibkr_paxos_long_midpoint', 'kraken_public', 'tvr_default_binance', 'yfinance']`.
- Provider symbols: `['BINANCE:BTCUSDT', 'BTC-USD', 'BTC.PAXOS', 'BTCUSDT', 'XBTUSD']`.
- Timeframes: `['1h']`.
- Parent roots in rows: `['Bull', 'Range']`.
- BBN max canonical probabilities: `{'range': 0.747688, 'stress': 0.177544, 'transition': 0.074769, 'trend': 0.0}`.
- Max Pre-Bayes confidence: `0.525086`.
- Execution ready/actionable rows: `0` / `0`.

## Checklist Result
- Checklist rows: `9`.
- Blocked rows: `6`.
- Gate: `board_a_completion_audit_v1=strict_objective_not_achieved_continue_no_update_goal`.

## Decision
- This is a completion audit only, not a promotion artifact.
- Provider coverage and ordered-chain evidence are present for the 115700 BTC 1h packet.
- The strict objective is not achieved: the current packet is BTC-only, 1h-only, not direct Manipulation evidence, below >=95% regime confidence, and execution remains observe/blocked.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T122208+0800-codex-121347-121607-board-a-completion-audit-v1/121347-121607-board-a-completion-audit-v1/board_a_completion_audit_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T122208+0800-codex-121347-121607-board-a-completion-audit-v1/121347-121607-board-a-completion-audit-v1/prompt_to_artifact_checklist_board_a_completion_audit_v1.csv`
- Provider/period summary: `docs/experiments/actionable-regime-confidence/runs/20260512T122208+0800-codex-121347-121607-board-a-completion-audit-v1/121347-121607-board-a-completion-audit-v1/provider_period_outcome_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T122208+0800-codex-121347-121607-board-a-completion-audit-v1/checks/board_a_completion_audit_v1_assertions.out`
