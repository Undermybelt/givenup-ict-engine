# Completion Audit

Objective: execute Board A from `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` using real Auto-Quant and ict-engine chain evidence, preserve provider breadth, and move useful `/tmp` artifacts into a durable repo subfolder.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Follow the named Board A file | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` cursor and ledger updated to `20260510T174651+0800-board-a-full-chain-readback` | covered |
| Do not invent; use real run artifacts | Source temp roots copied from `/tmp/ict-board-a-regime-confidence-20260510T174651`, `/tmp/ict-regime-chain-20260509T231052`, and `/tmp/ict-regime-branch-iteration-20260510-1` | covered |
| Operate Auto-Quant | `branch-chain/qqq-regime-branch-iteration/logs/10_auto_quant_run_tomac_hist.out`, `autoquant/autoquant-entry-windows-512-summary.json` | covered |
| Operate ict-engine | `branch-chain/qqq-regime-branch-iteration/logs/12_pre_bayes_status.out`, `logs/21_auto_quant_prior_init_apply.out`, `logs/46_execution_tree_trace_after_workflow_refresh_qqq.out` | covered |
| Pass through filter / pre-Bayes | `branch-chain/qqq-regime-branch-iteration/logs/12_pre_bayes_status.out` reports `gate=pass_neutralized` | covered |
| Pass through belief network / BBN | `branch-chain/qqq-regime-branch-iteration/logs/13_auto_quant_prior_init_dry_run.out` and `logs/21_auto_quant_prior_init_apply.out` report `evidence_value_gate_passed=true` | covered |
| Pass through CatBoost | `catboost/autoquant_entry_release_probe_512.json`, `catboost/autoquant_entry_release_leaksafe_probe_512.json`, and `branch-chain/.../catboost-path-ranker-qqq-replay-36-mature-only/catboost_model.cbm` | covered |
| Pass through execution tree | `execution-tree/entry_scan_512.tsv` and `execution-tree/entry_scan_512_summary.json`; audit count is 512 rows, 407 observe, 105 blocked, 0 pass/actionable | covered |
| Use IBKR | `provider/full-chain/loop4_ibkr_spy_15m_offline.csv` and `branch-chain/.../candles/ibkr_QQQ_1h.json` | covered |
| Use TradingViewRemix | `provider/full-chain/loop4_tradingview_qqq_1d_fetch.json` and `branch-chain/.../candles/tv_QQQ_1h.json` | covered |
| Use Yahoo/yfinance | `provider/full-chain/loop4_yf_nq_15m.csv`, `provider/current-board/spy_yahoo_1d.csv`, and `branch-chain/.../candles/yf_QQQ_1h.json` | covered |
| Use Kraken | `provider/full-chain/loop4_kraken_pf_xbtusd_15m.csv`, `provider/current-board/kraken_xbtusd_1d.csv`, and `branch-chain/.../candles/kraken_PF_XBTUSD_1h.json` | covered |
| Place results in a named subfolder suitable for later runs | `docs/experiments/actionable-regime-confidence/runs/20260510T174651/` | covered |
| Move useful `/tmp` artifacts into that subfolder | 330 hashed files under the durable run folder, with hashes in `checks/sha256sums.txt` | covered |
| Do not promote weak/leaky evidence | `evidence_packet.json` records `accepted_gate=none`, rejected leakage, and leak-safe `no_95_candidate` | covered |
| Complete A6 after repeated abstain | `target_schema_v2.json` resets target schema/regime family without relaxing thresholds | covered |

## Verification Commands

- `find docs/experiments/actionable-regime-confidence/runs/20260510T174651 -name '*.json' -print0 | xargs -0 -n1 jq empty`
- `jq -e '.target_schema_reset.thresholds_relaxed == false and (.next_action | contains("ProviderAgreementTrendExpansion"))' docs/experiments/actionable-regime-confidence/runs/20260510T174651/evidence_packet.json`
- `jq -e '.threshold_policy.thresholds_relaxed == false and .next_loop.id == "A-v2-1"' docs/experiments/actionable-regime-confidence/runs/20260510T174651/target_schema_v2.json`
- `awk -F'\t' ... docs/experiments/actionable-regime-confidence/runs/20260510T174651/execution-tree/entry_scan_512.tsv`
- `python3 -m unittest scripts.research.tests.test_execution_tree_guardrail_scan scripts.research.tests.test_selective_risk_control_probe scripts.research.tests.test_ofi_session_sidecar scripts.auto_quant_external.tests.test_next_slice_helpers scripts.research.tests.test_regime_conformal_calibration_report scripts.research.tests.test_regime_sidecar_pipeline`
- `git diff --check -- docs/plans/2026-05-10-actionable-regime-confidence-todo.md docs/experiments/actionable-regime-confidence/runs/20260510T174651/README.md docs/experiments/actionable-regime-confidence/runs/20260510T174651/evidence_packet.json docs/experiments/actionable-regime-confidence/runs/20260510T174651/target_schema_v2.json`

## Result

The loop is closed as an abstain, not a promotion. Board A now has a durable evidence packet and a v2 target-schema reset. The single next action is `A-v2-1`: generate v2 provider-agreement labels and rerun leak-safe chronological calibration.
