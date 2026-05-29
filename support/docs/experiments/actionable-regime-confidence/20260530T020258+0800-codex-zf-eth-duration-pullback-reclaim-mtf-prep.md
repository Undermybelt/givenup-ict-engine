# ZF ETH Duration Pullback Reclaim MTF Prep

created_at: 2026-05-30T02:02:58+0800
owner: codex
agent_name: codex-zf-eth-duration-pullback-reclaim-mtf-prep
status: terminalized_no_launch_prep_only_runtime_blocked
coordination_only: false
promotion_allowed: false
trade_usable: false
update_goal: false
same_tree_practical_closure: null

## Scope

Prep-only training packet for a new CBOT `ZF` 5-Year Treasury Note futures
factor branch. The packet is useful while current Board B runtime/claim owners
block new provider, IBKR, AutoQuant, Freqtrade, paper, sim, live, lifecycle, or
local backtest launches.

This is not the active XAU/GC ETH full-session TOMAC runtime, not the fresh 6E
London-open claim, not the existing ZB duration-trend prep, and not the earlier
Treasury curve sidecar prep.

## Evidence Surfaces

- `/tmp` workdoc: `/tmp/ict-engine-zf-eth-duration-pullback-reclaim-mtf-prep-20260530T020258+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T020258+0800-codex-zf-eth-duration-pullback-reclaim-mtf-prep.claim`
- Source directory: `/tmp/ict-engine-zf-eth-duration-pullback-reclaim-mtf-prep-20260530T020258+0800/sources`
- Terminal metrics: `/tmp/ict-engine-zf-eth-duration-pullback-reclaim-mtf-prep-20260530T020258+0800/checks/terminal_metrics.json`
- Terminal summary: `/tmp/ict-engine-zf-eth-duration-pullback-reclaim-mtf-prep-20260530T020258+0800/summaries/terminal_summary.json`

## Branch

```text
FUTURES -> TreasuryFutures -> ZF -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> MainRegime: DurationTrendContinuation -> SubRegime: CurveAlignedVolatilityPullback -> ProfitFactor: HtfSlopeReclaim -> ProfitFactor: AtrRiskManagedDurationPullback -> zf_eth_duration_pullback_reclaim_mtf_v1
```

session_scope: ETH/full_retained_session
rth_filter_applied: false

## Profit Hypothesis

Use ZF as the intermediate-duration Treasury futures leg. The future runner
should capture continuation after a duration trend is visible on higher frames,
but enter only after a short-term pullback/reclaim avoids chasing stretched
moves.

Candidate predicates:

- Main regime: 1d and 4h ZF slope are aligned, with 1h not counter-trending.
- Pullback: 15m/30m close temporarily below VWAP or EMA band while 4h trend
  remains intact.
- Reclaim: 1m/5m close reclaims VWAP/EMA with RVOL confirmation and ATR not
  expanding into disorder.
- Curve sidecar: ZN/ZB or 2s5s/5s10s state may be added only after real source
  labels exist; do not fabricate yield-curve labels.
- Exit: ATR bracket or trailing stop, plus time stop when 5m/15m slope breaks.

## Verified Cost Model

Verified from official IBKR pages/API responses in this slice:

- `ZF` maps through IBKR Products & Exchanges to `5 Year US Treasury Note -
  CBOT` with `FUT` sections for `JUN26`, `SEP26`, and `DEC26`.
- IBKR `webrest/search/contract-details` returned three futures conids, and
  `trsrv/secdef` returned `FUT` rows with `listingExchange=CBOT`,
  `currency=USD`, `ticker=ZF`, `multiplier=1000.0`, and tick increment
  `0.0078125`.
- IBKR futures commission page shows the low-volume USD futures commission tier
  as `USD 0.85/contract`.
- IBKR CBOT fee-recovery page shows `U.S. Treasury Futures ZF` with non-member
  exchange fee recovery `USD 0.65`, and regulatory fee recovery `All`
  non-member/IIP `USD 0.02`.

Component estimate under these assumptions:

```text
contract_multiplier=1000.0
tick_size=0.0078125
tick_value_usd=7.8125
commission_per_contract_per_side_usd=0.85
exchange_fee_recovery_per_contract_per_side_usd=0.65
regulatory_fee_recovery_per_contract_per_side_usd=0.02
estimated_all_in_per_contract_per_side_usd=1.52
estimated_all_in_round_turn_per_contract_usd=3.04
```

Direct CME contract-spec fetch failed from this host with `curl_exit=35` /
LibreSSL SSL syscall. For this packet, IBKR is the broker/cost authority and
provides both fee rows and broker-side FUT contract specs.

## Runtime Blocker

Same-turn compact audit at 2026-05-30T02:02:12+0800 reported
`status=needs_attention`, `live_factor_processes=1`,
`fresh_active_claims_without_live_process=1`, `promotion_allowed_true=0`, and
`trade_usable_true=0`.

Live owner: `/tmp/ict-engine-tomac-xau-eth-fullsession-vwap-washout-prep-20260530T014900+0800`.
Fresh no-live claim: `20260530T015410+0800-codex-6e-london-open-liquidity-sweep-vwap-reclaim-gate1.claim`.

## Future Launch Plan

Only after a fresh compact audit shows no active/fresh blockers and no live
factor processes, create/adapt a ZF runner and launch with 1m origin plus the
full shifted MTF ladder:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_zf1m_duration_pullback_reclaim_mtf_gate1_v1.py \
  --launch-aq \
  --root /tmp/ict-engine-zf-eth-duration-pullback-reclaim-mtf-run-<timestamp> \
  --timeframes 1m,5m,15m,30m,1h,4h,1d \
  --session-scope ETH/full_retained_session
```

Required before any promotion:

- Same-turn verified provider rows for ZF FUT with 1m origin and shifted
  `5m/15m/30m/1h/4h/1d` context.
- Cost survival against the verified IBKR ZF all-in model, not a generic bps
  proxy.
- AutoQuant Gate 1 and downstream readback from run-root artifacts.
- Pre-Bayes, BBN, path-ranker, execution-tree, feedback-update, and
  policy-training evidence if a candidate survives economics.
- Valid `same_tree_practical_closure` packet from
  `support/scripts/research/same_tree_practical_closure.py` before
  `promotion_allowed=true`, `trade_usable=true`, or `update_goal=true`.

## Terminal Decision

decision: terminalized_no_launch_prep_only_runtime_blocked

This packet prepares a non-duplicate ZF factor branch and verifies the ZF IBKR
cost model. It does not prove Gate 1 survival, AutoQuant admission, simulated or
paper execution, promotion, trade usability, or goal completion.

promotion_allowed: false
trade_usable: false
update_goal: false
