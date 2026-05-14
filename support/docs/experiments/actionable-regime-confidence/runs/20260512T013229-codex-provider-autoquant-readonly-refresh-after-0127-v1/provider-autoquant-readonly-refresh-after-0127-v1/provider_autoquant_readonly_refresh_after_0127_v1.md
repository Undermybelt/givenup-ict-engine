# Provider and Auto-Quant Read-Only Refresh After 0127 v1

- Gate result: `provider_autoquant_readonly_refresh_after_0127_v1=readiness_refreshed_no_promotion_roots_blocked`.
- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Selected providers: `yfinance=true:ready, ibkr_bridge=false:configured_runtime_unhealthy, kraken_cli=true:ready, ibkr=false:configured_runtime_unhealthy, kraken_public=false:configured_runtime_unhealthy, tradingview_mcp=false:configured_runtime_unhealthy, yfinance=true:ready`.
- Auto-Quant status: `dependency_ready_seed_required`; healthy `True`; data_ready `True`.
- Source-label root ready: `true`; R6 owner-export ready: `false`; R3 native-subhour ready: `false`; R5 recency ready: `false`.
- Canonical merge allowed: `false`; downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `false`.
- Accepted rows added: `0`; new confidence gate: false; strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. R3/R5/R6 roots mutated: false. Thresholds relaxed: false. Raw data committed: false. External requests sent: false. Trade usable: false.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T013229-codex-provider-autoquant-readonly-refresh-after-0127-v1/provider-autoquant-readonly-refresh-after-0127-v1/provider_autoquant_readonly_refresh_after_0127_v1.json`
- Selected provider CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T013229-codex-provider-autoquant-readonly-refresh-after-0127-v1/provider-autoquant-readonly-refresh-after-0127-v1/selected_provider_status_after_0127_v1.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T013229-codex-provider-autoquant-readonly-refresh-after-0127-v1/provider-autoquant-readonly-refresh-after-0127-v1/intake_root_status_after_0127_v1.csv`
- Provider stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T013229-codex-provider-autoquant-readonly-refresh-after-0127-v1/command-output/provider_status_agent.stdout.txt`
- Auto-Quant stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T013229-codex-provider-autoquant-readonly-refresh-after-0127-v1/command-output/auto_quant_status_json.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T013229-codex-provider-autoquant-readonly-refresh-after-0127-v1/checks/provider_autoquant_readonly_refresh_after_0127_v1_assertions.out`

Next:
- Preserve the Current Cursor next action for R6: acquire source-owned normal controls or explicit FLIP approval plus canonical merge before any downstream promotion rerun.
