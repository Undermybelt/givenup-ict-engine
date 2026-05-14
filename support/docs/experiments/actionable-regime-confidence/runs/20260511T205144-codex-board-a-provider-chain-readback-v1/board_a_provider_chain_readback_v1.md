# Board A Provider Chain Readback v1

Run ID: `20260511T205144+0800-codex-board-a-provider-chain-readback-v1`

- Gate result: `board_a_provider_chain_readback_v1=providers_and_chain_rerun_source_rows_still_missing`
- Outbox rows checked: `9`; source rows acquired: `False`.
- Current intake-root audit: `docs/experiments/actionable-regime-confidence/runs/20260511T205323-codex-current-goal-completion-audit-v37-after-live-public-recheck/completion-audit/current_goal_completion_audit_v37_intake_roots.csv`.
- Ready intake roots: `0/4`; existing roots: `['/tmp/ict-engine-direct-manipulation-row-intake']`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Provider Readback

| Surface | Status | Artifact |
|---|---|---|
| `provider_status_agent` | `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/provider_status_agent.json` |
| `provider_status_yfinance` | `live_runtime:1/1 ready | market_data:1/1 ready` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/provider_status_yfinance.json` |
| `provider_status_tradingview_mcp` | `market_data:1/1 ready` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/provider_status_tradingview_mcp.json` |
| `provider_status_ibkr` | `market_data:0/1 ready` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/provider_status_ibkr.json` |
| `provider_status_kraken_cli` | `local_runtime:1/1 ready` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/provider_status_kraken_cli.json` |
| `provider_status_kraken_public` | `market_data:0/1 ready` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/provider_status_kraken_public.json` |

## Provider Fetches

| Fetch | ok/error | rows | range | Artifact |
|---|---:|---:|---|---|
| `harness_yfinance_qqq_1d_fetch` | `1/0` | `20` | `2026-04-13T13:30:00Z..2026-05-08T13:30:00Z` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/harness_yfinance_qqq_1d_fetch.json` |
| `harness_tradingview_qqq_1d_fetch` | `1/0` | `20` | `2026-04-13T13:30:00Z..2026-05-08T13:30:00Z` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/harness_tradingview_qqq_1d_fetch.json` |
| `harness_ibkr_qqq_1d_fetch` | `0/0` | `0` | `..` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/harness_ibkr_qqq_1d_fetch.out` |
| `kraken_cli_xbtusd_1h_ohlc` | `1/0` | `721` | `1775912400..1778504400` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/provider/kraken_cli_xbtusd_1h_ohlc.json` |

## Chain Readback

| Command | Exit | Artifact | First line |
|---|---:|---|---|
| `auto_quant_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/chain-readback/auto_quant_status.json` | `{` |
| `auto_quant_run_help` | `2` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/chain-readback/auto_quant_run_help.out` | `` |
| `analyze_bull_bundle_readonly` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/chain-readback/analyze_bull_bundle_readonly.json` | `{` |
| `pre_bayes_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/chain-readback/pre_bayes_status.json` | `{` |
| `policy_training_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/chain-readback/policy_training_status.json` | `{` |
| `workflow_status_execution_candidate` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/chain-readback/workflow_status_execution_candidate.json` | `{` |
| `export_structural_path_ranking_target` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205144-codex-board-a-provider-chain-readback-v1/chain-readback/export_structural_path_ranking_target.json` | `{` |

## Interpretation

- yfinance, TradingViewRemix/TradingView MCP, IBKR status, and Kraken CLI were checked in this run.
- The ict-engine read-only path was rerun through analyze, Pre-Bayes status, policy/CatBoost path-ranking status, workflow execution-candidate status, and structural path-ranking export.
- Auto-Quant was touched through `auto-quant-status` and the local runtime help probe; `run.py --help` still exits through the known empty default strategy directory, so this is not treated as a data blocker.
- Provider OHLCV and read-only downstream traces do not supply source-owned MainRegimeV2 labels, native sub-hour labels, recency-extension source labels, or direct Manipulation positive/control rows.
- The latest v37 intake audit shows the direct Manipulation root exists with public positives/provenance, but it is still missing matched negative controls; the other three intake roots remain absent.

## Next

- Populate the four fail-closed intake roots with source-owned or owner-approved rows/provenance, then rerun the R2/R3/R4/R5/R6 verifiers and only then rerun BBN/CatBoost/execution-tree gates.
