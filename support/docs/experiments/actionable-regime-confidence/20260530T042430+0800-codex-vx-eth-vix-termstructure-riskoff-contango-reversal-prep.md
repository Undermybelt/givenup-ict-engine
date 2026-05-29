# VX ETH VIX Term Structure Risk-Off Contango Reversal Prep

created_at: 2026-05-30T04:24:30+0800
agent_name: codex-vx-eth-vix-termstructure-riskoff-contango-reversal-prep
status: terminalized_no_launch_prep_only_cost_source_reserve
promotion_allowed: false
trade_usable: false
update_goal: false

## Purpose

Preserve official source and cost material for a future VIX futures (VX/CFE)
ETH/full-session Gate 1 attempt while current Board B runtime and claims block
provider, IBKR historical, AutoQuant, Freqtrade, paper, sim, and lifecycle work.

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
Root symbol: VX / Cboe Volatility Index futures
Session scope: ETH/full retained tradable session
RTH filter applied: false
Origin/context target: 1m plus shifted 5m/15m/30m/1h/4h/1d

## Collision Readback

Before this packet, compact claim audit reported `status=needs_attention`, with
two valid active claims and one live factor process. The blocking lanes were the
fresh 6C/ZW claims and a live EUR/6E prep runtime root. This packet therefore
did not launch any runtime or historical-data command.

## Official Evidence

Same-turn official HTTP readbacks:

- Cboe VX contract specs: HTTP 200.
- Cboe VIX futures overview: HTTP 200.
- Cboe VIX term structure page: HTTP 200.
- Cboe U.S. futures hours: HTTP 200.
- Cboe CFE fee schedule: HTTP 200.
- IBKR futures commissions: HTTP 200.
- IBKR CFE fee recovery: HTTP 200 at `CBOE.php`.
- Guessed IBKR `CFE.php`: HTTP 404 and ignored.

Extracted fields:

- VX multiplier: USD 1000 per index point.
- VX default tick: 0.05 index points, USD 50 per contract.
- Cboe hours: regular 08:30-15:00 America/Chicago; extended windows 17:00
  previous day-08:30 and 15:00-16:00 America/Chicago.
- Cboe CFE customer transaction fee: VX weekly and monthly both USD 1.51.
- IBKR USD futures commission tier <= 1000 contracts: USD 0.85/contract/side.
- IBKR CFE VIX exchange fee recovery: USD 1.51/contract/side.
- IBKR CFE NFA regulatory fee recovery: USD 0.02/contract/side.

Partial declared IBKR/CFE/VIX fee assumption: USD 2.38/contract/side and USD
4.76/contract round turn before slippage and account/routing-specific details.

## Terminal Classification

`cost_model_status=cost_model_unverified` remains true because the exact
broker-side contract symbol, actual account/pricing applicability,
routing/liquidity flags, slippage model, selected VX contract month/roll rule,
and same-turn nonzero provider rows were not verified.

No provider rows, no IBKR historical fetch, no AutoQuant, no Freqtrade, no local
backtest, no Pre-Bayes/BBN/path-ranker/execution-tree, no paper/sim/live, and no
same-tree practical closure were produced.

Artifacts:

- Workdoc: `/tmp/ict-engine-vx-eth-vix-termstructure-riskoff-contango-reversal-prep-20260530T042430+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T042430+0800-codex-vx-eth-vix-termstructure-riskoff-contango-reversal-prep.claim`
- Evidence JSON: `support/docs/experiments/actionable-regime-confidence/runs/20260530T042430+0800-codex-vx-eth-vix-termstructure-riskoff-contango-reversal-prep-v1/checks/source_cost_readback_20260530T042430+0800.json`
- Terminal packet: `support/docs/experiments/actionable-regime-confidence/runs/20260530T042430+0800-codex-vx-eth-vix-termstructure-riskoff-contango-reversal-prep-v1/summaries/terminal_packet.md`
