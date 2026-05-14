# Regime Root Provider/Downstream Readback Corrected v2

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T061349+0800-codex-board-b-regime-root-provider-downstream-readback-corrected-v2`

Purpose: rerun the malformed downstream/status portions of `20260512T060837+0800-codex-board-b-regime-root-provider-downstream-readback-v1` with explicit `--symbol`, explicit `--state-dir`, and run-local provider fetch output paths.

Scope:
- No `HTF=1d`, `MTF=4h`, or `LTF=1h` path was selected.
- No Auto-Quant training was run.
- No canonical merge was run.
- No source/control root was unlocked or mutated.
- No promotion was allowed.
- `update_goal` remains false.

Corrected command result:
- `17/18` command families exited `0`.
- `10_ibkr_aapl_1h` exited `2` because `uv` could not fetch `ib-async` from PyPI after retries.
- The previously malformed empty `--symbol` and `--state-dir` commands now have valid arguments for `B2R_NQ_COST_CRISIS_REPAIR_032157` and `state_combined_v1`.
- The previous provider fetch commands that wrote to `/yfinance_qqq_1h.csv` and `/kraken_public_xbtusd_1h.csv` were rerun with run-local output files.

Provider readback:
- `provider-status --provider yfinance --agent` exited `0`; yfinance was ready for live runtime and market data.
- Corrected yfinance QQQ 1h fetch exited `0` and wrote `197` data rows.
- `provider-status --provider tradingview_mcp --agent` still reported the catalog probe as unhealthy, but the explicit local-stdio TradingViewRemix harness fetch exited `0` and returned `21` rows for `NASDAQ:QQQ`.
- `provider-status --provider kraken_public --agent` still reported missing Python provider dependencies, but the corrected public Kraken kline fetch exited `0` and wrote `721` data rows for `XBTUSD` 1h.
- `provider-status --provider kraken_cli --agent` exited `0` and reported `kraken_cli` ready.
- `provider-status --provider ibkr --agent` exited `0` but kept IBKR market data pending because runtime dependencies are missing even though the gateway is reachable. The explicit IBKR fetch did not complete because `uv` could not fetch `ib-async`.

Downstream readback:
- `auto-quant-status` exited `0`, with `status=dependency_ready_data_missing`, `dependency_healthy=true`, and `data_ready=false`.
- `pre-bayes-status` exited `0`, with `latest_gate_status=observe_only`.
- The Pre-Bayes filtered assignments preserved `regime_bundle_branch_path_count=5`; read-only BBN evidence fields were visible and `read_only_regime_bbn_trade_usable=true`, but `regime_bundle_bbn_application_status=skipped`.
- `policy-training-status` exited `0`; structural path-ranking runtime was enabled and candidate-set ready, but validation stayed unready: `raw_scored_mature=0/30`, `production_validation=0/30`, and `observation_validation=0/30`.
- `export-structural-path-ranking-target` exited `0`, with `rows=5`, `history_rows=10`, `mature_rows=0`, and `history_mature_rows=0`.
- `workflow-status --phase structural-recommended-path-bundle` exited `0` and selected the exact branch path `Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72`.
- The structural workflow next step remains `ask_user_choose_historical_data` with `blocked_reason=user_selected_historical_data_missing` and `user_input_required=true`.
- `workflow-status --phase execution-candidate` exited `0`; the execution candidate is not actionable, has `candidate_status=execution_blocked`, `pre_bayes_gate_status=observe_only`, `ready=false`, and `execution_readiness=0.3210541039505038`.

Interpretation:
- This corrected readback repairs the malformed-command surface of `060837`.
- It provides fresh provider/readback evidence across yfinance, TradingViewRemix, Kraken, IBKR status, Auto-Quant status, Pre-Bayes, BBN read-only branch assignments, CatBoost/path-ranker surfaces, and execution-candidate surfaces.
- It is not selected-data profitability evidence.
- It does not create nonzero mature rooted selected observations.
- It does not satisfy production or observation validation for CatBoost/path-ranking.
- It does not make the execution tree admissible.

Gate:
- `count_once:061349_regime_root_provider_downstream_readback_corrected_v2`.
- `corrected:060837_empty_symbol_state_dir_and_root_output_paths`.
- `provider_fetch:yfinance_rows_197`.
- `provider_fetch:tradingview_rows_21`.
- `provider_fetch:kraken_public_rows_721`.
- `provider_fetch:ibkr_fetch_failed_dependency_download`.
- `fail_closed:auto_quant_data_ready_false`.
- `fail_closed:pre_bayes_gate_observe_only`.
- `fail_closed:ranker_validation_0_of_30`.
- `fail_closed:execution_candidate_execution_blocked`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `update_goal=false`.

Next:
- Keep `034002` as the fail-closed cursor.
- The next qualifying Board B action still requires explicit user selection of exactly one recorded path, `HTF=1d`, `MTF=4h`, or `LTF=1h`, plus valid source/control unlock before selected-data Auto-Quant/factor-research can continue through filter / Pre-Bayes -> BBN -> CatBoost / path-ranking -> execution tree while preserving the exact `regime_profit_branch_path`.
