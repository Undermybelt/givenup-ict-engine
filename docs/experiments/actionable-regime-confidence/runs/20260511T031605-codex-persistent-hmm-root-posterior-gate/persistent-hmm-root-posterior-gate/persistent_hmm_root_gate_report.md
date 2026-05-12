# Persistent HMM Root Posterior Gate

Run id: `20260511T031605+0800-codex-persistent-hmm-root-posterior-gate`.

## Decision

- Gate result: `blocked_persistent_hmm_root_posterior_gate_below_95`
- Accepted new MainRegimeV2 roots: none
- Effective accepted roots after retained prior: Crisis
- Missing roots: Bull, Bear, Sideways, Manipulation
- Runtime code changed: `false`
- Thresholds relaxed: `false`

## Inputs

- `breadth_sector`: `docs/experiments/actionable-regime-confidence/runs/20260511T030516-codex-breadth-sector-root-gate/breadth-sector-gate/breadth_sector_root_feature_table.csv`
- `cboe_options_vol`: `docs/experiments/actionable-regime-confidence/runs/20260511T030759-codex-cboe-options-vol-root-gate/options-vol-gate/cboe_options_vol_root_feature_table.csv`

## Parent Root Results

| Root | State | Cal support | Cal LCB | Test support | Test LCB | Test precision | Test coverage | Blockers |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | blocked | 1389 | 0.374831 | 1728 | 0.286552 | 0.307870 | 0.241814 | calibration_wilson95_below_0_95, test_wilson95_below_0_95, ece_above_0_05 |
| Bear | blocked | 293 | 0.231563 | 275 | 0.157002 | 0.200000 | 0.038483 | calibration_wilson95_below_0_95, test_wilson95_below_0_95, ece_above_0_05 |
| Sideways | blocked | 1973 | 0.317025 | 1847 | 0.215677 | 0.234434 | 0.258466 | calibration_wilson95_below_0_95, test_wilson95_below_0_95, ece_above_0_05 |

## Model Policy

- Model family: supervised Gaussian HMM forward filter with train-only transition/emission estimates.
- Candidate labels: active MainRegimeV2 parent labels only: `Bull`, `Bear`, `Sideways`; `Crisis` and `UnknownOrMixed` are hidden competing states but not reissued here.
- Feature policy: current/past numeric fields only; `future_`, `next_`, root labels, identifiers, and raw OHLCV price columns are blocked as predictors.
- Threshold policy: posterior threshold selected on chronological calibration only, then held-out test is read once.
- Manipulation policy: not evaluated because these panels do not contain direct event/order-lifecycle/L2 evidence.

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T031605-codex-persistent-hmm-root-posterior-gate/persistent-hmm-root-posterior-gate/persistent_hmm_root_gate_report.json`
- Summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T031605-codex-persistent-hmm-root-posterior-gate/persistent-hmm-root-posterior-gate/persistent_hmm_root_gate_summary.csv`
- Full scores CSV: pruned by `docs/experiments/actionable-regime-confidence/runs/20260511T142928-codex-negative-raw-prune-v6/cleanup/negative_raw_prune_v6_manifest.md`
- Score sample CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T031605-codex-persistent-hmm-root-posterior-gate/persistent-hmm-root-posterior-gate/persistent_hmm_root_score_sample.csv`
