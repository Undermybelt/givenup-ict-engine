# Options Pressure Dealer-Stress Source Intake - 2026-05-30

Use this when a future ict-engine profitability-factor lane wants to add
NQ/ES options pressure, dealer stress, pinning, IV/skew, put-call, open
interest, or option-volume evidence as a sidecar.

## Session Evidence

Waiting-window packet:

- repo packet: `support/docs/experiments/actionable-regime-confidence/20260530T024744+0800-codex-nq-es-options-pressure-dealer-stress-source-intake.md`
- workdoc: `/tmp/ict-engine-nq-es-options-pressure-dealer-stress-source-intake-20260530T024744+0800/workdoc.md`
- terminal metrics: `/tmp/ict-engine-nq-es-options-pressure-dealer-stress-source-intake-20260530T024744+0800/checks/terminal_metrics.json`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T024744+0800-codex-nq-es-options-pressure-dealer-stress-source-intake.claim`

The packet was created while compact audit reported a fresh CL/WTI prep claim,
a fresh MGC local-screen claim, and a live NQ regression-channel prescreen. No
provider, IBKR, Auto-Quant, Freqtrade, paper/sim/live, lifecycle, local screen,
or downstream command was launched. The claim was terminalized immediately as
`terminalized_no_launch_source_intake_only`.

## Source Checks

Crossref returned matching DOI metadata for:

- Pan and Poteshman, `The Information in Option Volume for Future Stock Prices`, DOI `10.1093/rfs/hhj024`.
- Garleanu, Pedersen, Poteshman, `Demand-Based Option Pricing`, DOI `10.1093/rfs/hhp005`.
- Ni, Pearson, Poteshman, `Stock price clustering on option expiration dates`, DOI `10.1016/j.jfineco.2004.08.005`.

Official-data probes:

- CBOE broad daily options market-statistics page returned HTTP `200` after redirect.
- CME NQ and ES options contract-spec pages failed from this host with TLS EOF.

Therefore the data source remains unverified for an NQ/ES futures-options
sidecar. The paper metadata is useful as hypothesis support only; it is not a
runtime data contract.

## Reusable Guardrail

Options-pressure/dealer-stress sidecars must use real historical option fields:
option volume, open interest, IV, skew, put-call pressure, broker paper fields,
or another timestamped source that is known before the parent entry. Do not
fabricate Greeks, GEX, IV, skew, option volume, or open interest from 1m OHLCV
bars. Do not backtest a current options-chain snapshot as history. Do not
substitute broad CBOE daily equity-options statistics for NQ/ES futures-options
pressure unless a future source contract explicitly maps that field.

Treat the candidate as a sidecar only:

```text
TransitionRisk -> OptionsPressure -> DealerStressSidecar -> ParentTrendSkipOrThrottle -> nq_es_options_pressure_dealer_stress_sidecar_v1
```

It has no standalone entry. It may only skip, throttle, shorten, or require
stronger RRR for an already owned parent NQ/ES trend, MIM, or carryover branch.
If cadence rises after the sidecar, reject the design.

## Admission Rule

Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
until all are true:

- compact claim audit is clear for the owned parent lane;
- a historical options sidecar is verified with timestamp availability before
  entry;
- parent futures cost model is verified;
- ETH/full retained-session rows outside RTH are proven for the parent data;
- the same-root practical lifecycle evidence passes the normal ict-engine gates.
