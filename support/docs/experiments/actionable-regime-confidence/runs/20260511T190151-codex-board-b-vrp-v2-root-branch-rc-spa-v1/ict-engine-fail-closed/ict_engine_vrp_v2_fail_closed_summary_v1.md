# ict-engine VRP V2 Fail-Closed Readback v1

Run id: `20260511T190151+0800-codex-board-b-vrp-v2-root-branch-rc-spa-v1`.

## Decision

- Promotion state: `fail_closed`
- Reason: VRP V2 branch RC-SPA rejected before downstream promotion.
- ict-engine import mode: `dry_run`
- Trades total: `815`
- Trades applied in dry-run preview: `600`
- Trades invalid: `215`
- Pre-Bayes: `unavailable`
- Policy/path-ranker: `structural path ranking target export missing`
- Workflow: `no_workflow_state`

## Provider Readback

- yfinance: `ready` for live runtime and market data.
- TradingView MCP: `ready` with MCP URL and API key available.
- IBKR: `configured_runtime_unhealthy`; gateway reachable but runtime dependencies missing.
- Kraken CLI: `ready`.
- Kraken public: `configured_runtime_unhealthy`; Python provider dependencies missing.

## Artifacts

- Branch RC-SPA report: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/branch-rc-spa/vrp_v2_root_branch_rc_spa_report_v1.md`
- Wire JSONL: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/ict-engine-fail-closed/vrp_v2_real_trades_wire_v1.jsonl`
- Dry-run import: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/ict-engine-fail-closed/logs/auto_quant_ingest_real_trades_dry_run.out`
- Pre-Bayes readback: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/ict-engine-fail-closed/logs/pre_bayes_status_human.out`
- Policy readback: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/ict-engine-fail-closed/logs/policy_training_status_human.out`
- Workflow readback: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/ict-engine-fail-closed/logs/workflow_status_human.out`

## Next

VRP cannot be promoted from aggregate Sharpe or the prior runtime-closure artifacts. It needs either a true multi-root parameter matrix that passes every required branch gate, or direct scoped Manipulation rows plus a refreshed branch RC-SPA run.
