# VX ETH VIX Term Structure Risk-Off Contango Reversal Prep Terminal Packet

created_at: 2026-05-30T04:33:00+0800
agent_name: codex-vx-eth-vix-termstructure-riskoff-contango-reversal-prep
factor_id: vx_eth_vix_termstructure_riskoff_contango_reversal_v1
decision: terminalized_no_launch_prep_only_cost_source_reserve
status: terminalized
promotion_allowed: false
trade_usable: false
update_goal: false

## Branch

```text
StressExpansion
-> VixFuturesTermStructureShock
-> ContangoCompressionRiskOffTransition
-> FrontMonthVolatilityReversal
-> AtrRiskManagedMtfContinuation
-> vx_eth_vix_termstructure_riskoff_contango_reversal_v1
```

Market: FUTURES
Product: volatility futures
Exchange: CFE
Root: VX / Cboe Volatility Index futures
Session scope: ETH/full retained tradable session
RTH filter applied: false
Origin/context: 1m origin plus shifted 5m/15m/30m/1h/4h/1d context target

## Why No Launch

Same-turn compact audit before this lane showed `status=needs_attention`, with
active 6C and ZW claims and a live EUR/6E prep runtime root. This packet did not
start provider-status, provider fetch, IBKR historical, AutoQuant, Freqtrade,
paper, sim, live, lifecycle, downstream, or local backtest commands.

## Official Source Readback

- Cboe VX contract specs: HTTP 200.
- Cboe VIX futures overview: HTTP 200.
- Cboe VIX term structure page: HTTP 200.
- Cboe U.S. futures hours: HTTP 200.
- Cboe CFE fee schedule: HTTP 200.
- IBKR futures commission page: HTTP 200.
- IBKR CFE fee recovery page: HTTP 200 at `CBOE.php`.
- Guessed IBKR `CFE.php` URL: HTTP 404; no fee inferred from that page.

## Extracted Fields

- VX multiplier: USD 1000 per index point.
- VX default tick: 0.05 index points, USD 50 per contract.
- Regular hours: 08:30-15:00 America/Chicago.
- Extended windows: 17:00 previous day-08:30 and 15:00-16:00 America/Chicago.
- Cboe CFE customer transaction fee for VX monthly/weekly: USD 1.51.
- IBKR USD futures commission tier <= 1000 contracts: USD 0.85/contract/side.
- IBKR CFE VIX exchange fee recovery: USD 1.51/contract/side.
- IBKR CFE NFA regulatory fee recovery: USD 0.02/contract/side.

Declared IBKR/CFE/VIX assumption partial fee: USD 2.38/contract/side, USD 4.76
round turn before slippage and any account/routing-specific differences.

## Classification

`cost_model_status=cost_model_unverified` because broker-side exact contract
symbol, actual account/pricing applicability, routing/liquidity flags, slippage,
selected VX contract month/roll rule, and same-turn nonzero provider rows are
not verified.

This is useful source/cost reserve material only. It is not Gate 1, not economic
evidence, not provider proof, not AutoQuant proof, and not practical lifecycle
evidence.

Evidence JSON:
`support/docs/experiments/actionable-regime-confidence/runs/20260530T042430+0800-codex-vx-eth-vix-termstructure-riskoff-contango-reversal-prep-v1/checks/source_cost_readback_20260530T042430+0800.json`
