# Recorded-MTF Provider Fullchain Readback v1

Run id: `20260512T101020+0800-codex-board-b-recorded-mtf-provider-fullchain-readback-v1`

Mode: `incubation_only`

## Scope

This is an additive readback for the recorded-MTF `SRC_ROOT_CARRY_LONG_220646` branch. It does not edit the Current Cursor, does not select HTF/MTF/LTF on behalf of the user, does not approve source/control evidence, does not promote a candidate, and does not call `update_goal`.

Source state was copied from:

`docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

Isolated readback state:

`docs/experiments/actionable-regime-confidence/runs/20260512T101020+0800-codex-board-b-recorded-mtf-provider-fullchain-readback-v1/state_recorded_mtf_fullchain_v1`

Related provider acquisition packet:

`docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1`

## Command Exits

- `01_provider_status_agent`: `0`
- `02_auto_quant_status_source`: `0`
- `03_auto_quant_adoption_review_source`: `0`
- `04_auto_quant_prior_init_dry_run`: `0`
- `05_pre_bayes_status_refresh`: `0`
- `06_policy_training_status_agent`: `0`
- `07_workflow_structural_bundle`: `0`
- `08_workflow_execution_candidate`: `0`
- `09_workflow_full_agent`: `0`
- `10_auto_quant_prepare_isolated`: `1`
- `11_auto_quant_status_isolated`: `0`
- `12_auto_quant_prepare_isolated_metadata_fixed`: `1`
- `13_auto_quant_status_isolated_metadata_fixed`: `0`

## Provider Readback

Provider acquisition packet `100419` produced concrete provider rows:

- yfinance `NQ=F` 1h: `642` rows, `2026-04-01 00:00:00+00:00` to `2026-05-11 23:00:00+00:00`
- Kraken spot `XBTUSD` 1h: `721` rows, `2026-04-12 02:00:00+00:00` to `2026-05-12 02:00:00+00:00`
- Binance spot `BTCUSDT` 1h: `985` rows
- Bybit linear `BTCUSDT` 1h: `985` rows

Provider blockers recorded in the same packet:

- TradingViewRemix / `tradingview_mcp`: credentials were present, but live OHLCV fetch failed.
- IBKR: local gateway was reached, but the specific `NQ` futures contract request failed as an unknown contract; provider-status also reports missing runtime modules.

Fresh provider-status in this readback exited `0` and reported:

- `yfinance`: ready
- `kraken_cli`: ready
- `tradingview_mcp`: not ready in this runtime
- `ibkr` / `ibkr_bridge`: not ready; gateway reachable but runtime deps missing
- `kraken_public`, `binance_public`, `bybit_public`: not ready through the repo provider-status path because system Python provider deps are missing

## Auto-Quant Readback

`auto-quant-status` on the source recorded-MTF state reported `dependency_ready_data_missing`; adoption review reported `prepare_required`.

`auto-quant-prior-init --dry-run` on the isolated state exited `0` and consumed the recorded strategy library as BBN prior evidence. It applied five strategies from `recorded_nq_precision_fixed_v1`:

- `RecordedBranchDailyPulse`: `478` trades
- `RegimeRootPulseBranch`: `300` trades
- `RegimeRsiRelief`: `2` trades
- `RegimeTrendCarry`: `30` trades
- `RegimeVolBreakout`: `33` trades

The dry-run reported `evidence_value_gate_passed=true`.

The first isolated prepare attempt exposed stale dependency metadata: copied `auto_quant_dependency.json` still pointed `managed_dir` at the source run. After fixing only the copied metadata to point at this run's copied `.deps/auto-quant`, the metadata-fixed prepare attempted the real Freqtrade/Binance path and failed with DNS resolution for `api.binance.com`. Final isolated status stayed `dependency_ready_data_missing`.

## Downstream Chain

Pre-Bayes:

- `gate=pass_neutralized`
- `soft_evidence=yes`
- long probability `0.549`
- short probability `0.540`
- MTF bias `bullish`
- alignment `0.770`
- entry alignment `0.863`

BBN:

- Auto-Quant prior dry-run was callable and evidence-gated.
- Pre-Bayes evidence assignments preserved `regime_bundle_branch_paths_json` with the exact Crisis branch path.
- The chain remains non-promoting because this is a dry-run/readback and AQ prepare data is still not ready.

CatBoost/path-ranker:

- structural path-ranker runtime `enabled=true`
- runtime status `enabled_candidate_set_ready`
- trainer artifact `model_family=catboost`
- trainer trained rows `12329`
- production validation `286/30`
- observation validation `48/30`
- structural bundle consumed `path_ranker_raw_score=0.65` with `path_ranker_runtime_source=history_path`

Execution tree:

- structural path preserved:
  `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- execution-candidate preserved the same `path_id`
- `pre_bayes_gate_status=pass_neutralized`
- `execution_gate_status=execution_observe_only`
- `execution_readiness=0.4504361163104953`
- `ready=false`
- `review_status=observe`
- `review_reason=structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`

## Decision

Gate: `incubation_only:recorded_mtf_provider_fullchain_readback_v1`.

The rooted branch path survives Pre-Bayes / BBN evidence / CatBoost path-ranking / execution-candidate readback. This is useful plumbing evidence, but it is not promotion evidence.

Promotion remains blocked:

- `fail_closed:auto_quant_prepare_data_missing`
- `fail_closed:binance_dns_prepare_failure`
- `fail_closed:execution_observe_only`
- `fail_closed:pre_bayes_gate_not_hard_ready`
- `fail_closed:source_control_evidence_acquired_false`
- `fail_closed:selected_history_user_explicit_false`

`promotion_allowed=false`.

`update_goal=false`.

## Next

Use `100419` provider rows and this readback as non-promoting input material. The next non-duplicative slice is to pre-seed a fully isolated Auto-Quant workspace from already acquired provider CSVs or recorded-history rows, bypassing live Binance prepare DNS, then rerun the same branch-preserving downstream chain only if that AQ run creates nonzero mature rooted branch observations.
