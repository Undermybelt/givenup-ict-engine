# Provider-Provenanced ETH Kraken MTF v1

Run id: `20260512T125753+0800-codex-provider-provenanced-eth-kraken-mtf-v1`

## Scope

Kraken-only ETH multi-timeframe provider-provenance diagnostic for Board A. This run proves a real provider data path and ict-engine readback on ETH/Kraken, but it is not a six-provider AQ authority packet and cannot satisfy Board A acceptance by itself.

## Evidence

- Provider/status command: `command-output/provider_status_agent.out`
- Kraken fetch/convert outputs: `command-output/fetch_kraken_ethusd_1h.out`, `command-output/fetch_kraken_ethusd_4h.out`, `command-output/fetch_kraken_ethusd_1d.out`, plus matching convert outputs.
- Provider data files: `data/kraken_ethusd_1h.csv`, `data/kraken_ethusd_4h.csv`, `data/kraken_ethusd_1d.csv`, plus matching JSON/provenance files.
- Auto-Quant outputs: `command-output/auto_quant_status_after_prepare.out`, `command-output/factor_research_auto_quant_after_prepare.out`, `command-output/auto_quant_run_tomac.out`, `command-output/auto_quant_run_tomac.err`.
- ict-engine readbacks: `command-output/analyze_ethkraken_mtf.out`, `state_eth_kraken_mtf/ETH_KRAKEN/workflow_snapshot.json`, `state_ethkraken_mtf/ETHKRAKEN/workflow_snapshot.json`.

## Command Results

- Provider data fetches exited `0` for Kraken ETH/USD `1h`, `4h`, and `1d`; each CSV has `721` data rows.
- JSON conversion exited `0` for all three timeframes.
- ict-engine analyze exits were `0` for both `ETH_KRAKEN` and `ETHKRAKEN` state variants.
- `factor-research --backend auto-quant` exited `0` before and after Auto-Quant prepare, emitting an Auto-Quant handoff with `data_ready=true`.
- `auto-quant-prepare` exited `0`, and `auto-quant-status` reported `dependency_ready_data_ready`, `healthy=true`, `dependency_healthy=true`, and `data_ready=true`.
- Auto-Quant TOMAC execution did not produce measured strategy evidence: the plain workspace run failed with `ModuleNotFoundError: No module named 'freqtrade'`, while the prepared `uv --with ta-lib run_tomac.py` run failed with Freqtrade `OperationalException: No pair in whitelist`.

## Runtime Readback

- Pre-Bayes status stayed `pass_neutralized` with quality score `0.5574970918447152`.
- Canonical structural probabilities were trend `0.4460727525727625`, range `0.3107854494854475`, stress `0.16745597773596904`, and transition `0.075685820205821`.
- Market-state evidence reported `primary_regime=TrendExpansion`, `secondary_regime=BullTrendAcceleration`, and overall confidence `0.618`.
- Multi-timeframe readback covered `15m`, `1h`, and `1d`, with `1m`, `5m`, `30m`, and `4h` missing from the analyze coverage summary.
- Execution stayed non-admitting: `decision_summary=Observe only`, execution gate `execution_blocked`, execution readiness about `0.438`, and workflow blocked on `user_selected_historical_data_missing`.

## Decision

Gate: `kraken_mtf_provider_provenance_present_auto_quant_tomac_no_pair_no_promotion`.

This run is useful provider-provenanced Kraken/ETH MTF evidence and proves the managed Auto-Quant workspace can reach `dependency_ready_data_ready`, but it remains fail-closed for Board A:

- six-provider AQ authority false
- TOMAC measured strategy evidence false
- calibrated `>=95%` regime confidence false
- CatBoost/path-ranker promotion false
- execution-tree promotion false
- trade usable false
- promotion allowed false
- `update_goal=false`

## Next

Do not promote or repeat this Kraken-only shape as Board A acceptance. The useful follow-up is either a repaired Auto-Quant pair whitelist for this provider-provenanced MTF packet, or a six-provider packet that carries all required provider rows into Auto-Quant, Pre-Bayes/BBN, CatBoost/path-ranker, and execution-tree with calibrated `>=95%` confidence.
