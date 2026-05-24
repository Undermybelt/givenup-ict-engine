# Board B Threshold Review - 2026-05-24

Purpose: compact evidence packet for the Board B cost, transition, readiness,
validation, and provider-parity threshold review. This document is advisory
evidence only. Runtime truth remains in code, JSON/CSV artifacts, CLI output, and
state directories.

## Decision

Do not lower the current promotion thresholds.

The current gate shape remains reasonable:

- Cost: require exact-root `5bps/side` survival plus density before downstream
  promotion.
- Transition: require `transition_hazard < 0.60` before trade admission.
- Readiness: require stable `execution_readiness >= 0.65` before promotion.
- Validation: require raw-scored mature, production, and observation validation
  rows to reach `30/30`.
- Provider parity: use provider/current runtime parity as a promotion
  prerequisite where available; branch-local evidence without parity remains
  evidence or repair material, not live-practical.

No threshold was changed in this review. The only code repair is schema
recognition for current Gate 1 cost-stress rows so valid `5bps/side` survivors
are not misclassified as Gate 1 economics failures.

## External Source Readback

- Backtrader explicitly models slippage because backtests cannot guarantee real
  market conditions, and it exposes percentage/fixed slippage settings:
  `https://www.backtrader.com/docu/slippage/slippage/`.
- Freqtrade backtesting applies configurable fees on both entry and exit and
  fetches exchange pair/market fees by default:
  `https://www.freqtrade.io/en/stable/backtesting/`.
- QuantConnect LEAN documents slippage/reality models and warns that live
  results commonly deviate from backtests due to data, fills, brokerage, and
  modeling differences:
  `https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/slippage/key-concepts`
  and
  `https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/reconciliation`.
- Zipline models slippage as a function of historical volume share:
  `https://zipline.ml4trading.io/api-reference.html#module-zipline.finance.slippage`.
- Bailey, Borwein, Lopez de Prado, and Zhu's Probability of Backtest Overfitting
  paper supports treating backtest-selected strategies as overfit-prone unless
  validated out of sample:
  `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253`.
- Bailey and Lopez de Prado's Deflated Sharpe Ratio paper supports correcting
  selection bias/multiple testing before treating a positive backtest as a real
  finding:
  `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551`.
- Backtrader's Interactive Brokers live-trading docs recommend paper/TWS demo
  testing before production and note live broker behavior differs from simulated
  broker behavior:
  `https://www.backtrader.com/docu/live/ib/ib/`.

Implication: open-source engines and finance-ML literature support stricter,
not looser, gates around fees/slippage, out-of-sample validation, live/provider
reconciliation, and fail-closed paper/live readiness.

## Local Tmp Re-screen

Artifacts:

- Claim audit:
  `/tmp/ict-engine-boardb-claim-audit-20260524Tthreshold-review-rerun.json`
- Tmp terminal-metrics re-screen:
  `/tmp/ict-engine-boardb-tmp-threshold-rescreen-20260524Tthreshold-review.json`
- CRWD blocker report:
  `/tmp/ict-engine-crwd5m-threshold-blocker-report-20260524.json`
- ETN blocker report:
  `/tmp/ict-engine-etn5m-threshold-blocker-report-20260524.json`

Fresh claim audit summary:

- `total_claims=447`
- `terminalized_claims=407`
- `active_claims=40`
- `missing_run_roots=2`
- `live_factor_processes=0`
- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `status=needs_attention`

Tmp terminal-metrics re-screen summary:

- `scanned_terminal_metrics=70`
- `parse_errors=0`
- `exact_5bps_present=14`
- `feedback_allowed=3`
- `contract_violations=36`
- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `extension_complete_true=0`

## Evidence Or Repair Candidates

These candidates may enter evidence/repair queues. None is live-practical.

1. CRWD late-session hazard trim
   - Metrics:
     `/tmp/ict-engine-crwd5m-late-session-hazard-trim-fresh-gate1-20260523T063516+0800/checks/terminal_metrics.json`
   - Exact `5bps/side` survivors: 4
   - `execution_readiness=0.67`
   - `transition_hazard=0.5922228286125956`
   - `pda_hybrid_alignment=true`
   - `ranker_validation_ready=true`
   - Blocker: execution candidate is `no_trade`; validation rows are `0/30`
     for raw-scored mature, production, and observation.
   - Decision: `repair_same_root_validation_rows`.

2. IBKR S/5m PDA transition quality filter
   - Metrics:
     `/tmp/ict-engine-ibkr-s5m-pda-transition-quality-filter-gate1-20260523T102345+0800/checks/terminal_metrics.json`
   - Exact `5bps/side` survivors: `15m`, `4h`, `5m`
   - Contract violations: none in the threshold re-screen.
   - Blocker: branch-local only; extension incomplete and no current downstream
     practical readback in this review.
   - Decision: evidence/repair candidate only.

3. ETN/5m Gann HiLo quality
   - Metrics:
     `/tmp/ict-engine-ibkr-etn-electrical-equipment-gann-hilo-activator-5m-quality-exact-gate1-20260524T025913+0800/checks/terminal_metrics.json`
   - Exact `5bps/side` survivor: `ETN/5m/quality`
   - `rank_total_trade_count=123`
   - `execution_readiness=0.1808141633548176`
   - `transition_hazard=0.3692625258022143`
   - `pda_hybrid_alignment=true`
   - `ranker_validation_ready=false`
   - Blocker: execution candidate is `no_trade`; path ranker is visible but not
     used; validation rows are `0/30`; MTF/regime alignment conflicts remain.
   - Decision changed from false `drop_gate1_economics` to
     `repair_same_root_mtf_and_regime_alignment` after the cost-stress-row
     schema repair.

## Practical Verdict

Current tmp outputs can enter evidence/repair tracking, not live trading. The review
found `0` `promotion_allowed` and `0` `trade_usable` candidates after re-screen.
Lowering thresholds would promote artifacts that still fail validation,
execution materialization, provider/current-runtime parity, or extension
completion.
