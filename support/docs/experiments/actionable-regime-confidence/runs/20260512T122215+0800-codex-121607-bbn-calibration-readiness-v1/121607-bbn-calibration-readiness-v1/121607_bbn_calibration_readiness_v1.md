# 121607 BBN Calibration Readiness v1

Run id: `20260512T122215+0800-codex-121607-bbn-calibration-readiness-v1`
Source feedback packet: `20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1`
Source downstream chain: `20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1`
Source AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`

## Result
- Rows: `237`; wins `81`; losses `156`; win rate `0.341772`; loss rate `0.658228`.
- Candidate smoothed CPD: `{'win': 0.351456, 'breakeven': 0.031003, 'loss': 0.617541}` with alpha `30.0`.
- Gate: `fail_closed:candidate_only_no_production_bbn_update`.

## Gate Matrix
- `exact_root_feedback`: `pass`; 20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1 -> 20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1 -> 20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1; blocker `none`.
- `row_volume`: `pass`; 237 rows >= 30; blocker `none`.
- `provider_context`: `pass`; 6 providers: binance_public, bybit_public, ibkr_paxos_long_midpoint, kraken_public, tvr_default_binance, yfinance; blocker `none`.
- `branch_attribution`: `pass`; 2 branch paths; blocker `none`.
- `chronological_holdout`: `fail_closed`; provider windows overlap=True; no held-out chronological update artifact; blocker `needs disjoint calibration/test periods before BBN CPD mutation`.
- `cross_instrument`: `fail_closed`; symbols=['BINANCE:BTCUSDT', 'BTC-USD', 'BTC.PAXOS', 'BTCUSDT', 'XBTUSD']; blocker `only BTC-like instruments are represented`.
- `execution_admissibility`: `fail_closed`; ready=False actionable=False review=observe readiness=0.32853919817900823; blocker `execution tree stayed observe/execution_blocked`.
- `selected_history_source_control`: `fail_closed`; no selected-history/source-control unlock in source packet; blocker `cannot promote or mutate production likelihoods`.
- `bbn_cpd_update_authority`: `fail_closed`; candidate_only_chronological_smoothing_required; blocker `candidate-only chronological smoothing required`.

## Decision
- The negative packet is useful for BBN likelihood/CPD calibration queues and CatBoost hard-negative analysis.
- It is not sufficient for production BBN mutation because chronology, cross-instrument coverage, selected-history/source-control, and execution admissibility are still fail-closed.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T122215+0800-codex-121607-bbn-calibration-readiness-v1/121607-bbn-calibration-readiness-v1/121607_bbn_calibration_readiness_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T122215+0800-codex-121607-bbn-calibration-readiness-v1/derived/121607_bbn_calibration_gate_matrix_v1.csv`
- CPD candidate JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T122215+0800-codex-121607-bbn-calibration-readiness-v1/derived/121607_bbn_cpd_candidate_smoothed_v1.json`
- Provider windows JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T122215+0800-codex-121607-bbn-calibration-readiness-v1/derived/121607_provider_windows_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T122215+0800-codex-121607-bbn-calibration-readiness-v1/checks/121607_bbn_calibration_readiness_v1_assertions.out`
