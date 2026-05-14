# HMM/Markov Root Gate

Run id: `20260511T031433+0800-codex-hmm-markov-root-gate`

## Data

- yfinance symbols requested: BTC-USD, DBC, ETH-USD, GLD, HYG, IWM, LQD, QQQ, SPY, TLT, UUP, ^VIX, ^VIX3M.
- yfinance symbols available: BTC-USD, DBC, ETH-USD, GLD, HYG, IWM, LQD, QQQ, SPY, TLT, UUP, ^VIX, ^VIX3M.
- Derived feature rows: 25922.
- Raw provider CSV committed: false; cache path `/private/tmp/ict-regime-hmm-markov-root/yfinance_cross_asset_daily_close.csv`.
- Latent-state fit: deterministic train-only k-means Markov surrogate because `hmmlearn` / `sklearn` are not installed.
- Predictors blocked: `future_ret_label_only`, `future_range_label_only`, `root_label`, timestamps, identifiers, and label fields.

## Gate Results

- Bull: accepted_95=False, rule=`p_bull >= 0.228501228501`, cal_lcb=0.155983, test_lcb=0.173752, cal_support=1123, test_support=875, blockers=calibration_wilson95_below_0_95|test_wilson95_below_0_95|ece_above_0_05
- Bear: accepted_95=False, rule=`p_bull >= 0.228501228501`, cal_lcb=0.100823, test_lcb=0.082356, cal_support=1123, test_support=875, blockers=calibration_wilson95_below_0_95|test_wilson95_below_0_95
- Sideways: accepted_95=False, rule=`p_sideways >= 0.303875407461`, cal_lcb=0.112037, test_lcb=0.158337, cal_support=1759, test_support=2014, blockers=calibration_wilson95_below_0_95|test_wilson95_below_0_95|ece_above_0_05

## Decision

- Newly accepted active roots: none.
- Gate: `blocked_hmm_markov_root_gate_below_95`.
- Thresholds relaxed: false.
- Runtime code changed: false.
- Trade usable: false.

Train-only latent-state root posteriors did not close all missing MainRegimeV2 roots at the unchanged 95% held-out gate.

Next: Acquire labeled bull/bear/sideways regime-cycle data or true options/dealer-positioning history; avoid more proxy-only threshold scans, and keep Manipulation blocked until direct labels exist.
