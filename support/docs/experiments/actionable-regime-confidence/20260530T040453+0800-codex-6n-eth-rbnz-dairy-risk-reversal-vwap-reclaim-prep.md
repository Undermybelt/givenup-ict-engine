# 6N ETH RBNZ/Dairy Risk Reversal VWAP Reclaim Prep

created_at: 2026-05-30T04:04:53+0800
owner: codex
agent_name: codex-6n-eth-rbnz-dairy-risk-reversal-vwap-reclaim-prep
run_root: /tmp/ict-engine-6n-eth-rbnz-dairy-risk-reversal-vwap-reclaim-prep-20260530T040453+0800
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T040453+0800-codex-6n-eth-rbnz-dairy-risk-reversal-vwap-reclaim-prep.claim
status: terminalized_no_launch_prep_only_runtime_blocked
promotion_allowed: false
trade_usable: false
update_goal: false
same_tree_practical_closure: null

## Objective

Create a fresh ETH/full retained-session source-prep packet for a non-duplicate
FX-futures branch while a foreign live runtime blocks provider/AQ/IBKR launches.
This is not Gate 1 evidence and does not attempt to promote anything.

## Branch

canonical_branch_path:

```text
CommodityFXRiskTransition -> RbnzDairyRiskReversal -> AsiaLondonLiquidityStopRun -> VwapReclaimAfterDairyPolicyShock -> AtrRiskManagedMtfContinuation -> 6n_eth_rbnz_dairy_risk_reversal_vwap_reclaim_v1
```

labels:
- market: `FUTURES`
- product: `FXFutures`
- exchange: `CME`
- root_symbol: `6N / New Zealand Dollar futures`
- broker_side_symbol: unverified, candidate `NZD` only after IBKR contract-details proof
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: false
- origin_timeframe: `1m`
- context_ladder: shifted `5m/15m/30m/1h/4h/1d`

## Collision Guard

Same-turn compact audit reported `status=needs_attention` because of a foreign
live factor process under:

```text
/tmp/ict-engine-eur-eth-donchian-tsmom-volcarry-prep-20260530T005133+0800
```

Focused `ps` showed that root running a 6E/EUR local screen. This packet
therefore does not launch provider-status, IBKR historical fetch, AutoQuant,
Freqtrade, paper/sim/live, lifecycle, Pre-Bayes, BBN, CatBoost, path-ranker, or
execution-tree commands.

## Source And Cost Readback

- IBKR futures commission page returned HTTP 200 from
  `https://www.interactivebrokers.com/en/pricing/commissions-futures.php`.
  Same-turn readback showed the United States futures/futures-options USD table
  with first tier `USD 0.85/contract`, lower volume tiers, and exchange,
  regulatory, and overnight fee offsets.
- CME New Zealand Dollar contract-spec and CME FX pages failed from this host
  with curl/TLS or host fetch failures, so 6N multiplier, tick value, exchange
  fees, regulatory fees, and exact contract month are not verified.
- RBNZ official OCR decisions URL returned HTTP 403 from this host.
- GlobalDairyTrade product-results returned HTTP 200 and exposed GDT Price Index
  and product-results text. Treat it as a possible exogenous dairy-risk sidecar,
  not trade evidence.

Source evidence:

- `/tmp/ict-engine-6n-eth-rbnz-dairy-risk-reversal-vwap-reclaim-prep-20260530T040453+0800/source_evidence/source_cost_readback_20260530T040453+0800.json`
- `support/docs/experiments/actionable-regime-confidence/runs/20260530T040453+0800-codex-6n-eth-rbnz-dairy-risk-reversal-vwap-reclaim-prep-v1/checks/source_cost_readback_20260530T040453+0800.json`

## Planned Launch Shape After Runtime Clears

Only after a fresh compact audit and focused process table show no foreign
runtime, verify IBKR contract details and same-turn row truth:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact
ps -axo pid,ppid,etime,%cpu,%mem,command | rg 'factor|tomac|auto-quant|run_yf_us_equity|fetch_external|ibkr|freqtrade|paper|sim'
cargo run --quiet -- provider-status --provider ibkr --agent
python3 support/scripts/auto_quant_external/fetch_external.py ibkr-historical \
  --symbol <VERIFIED_IBKR_NZD_OR_6N_SYMBOL> \
  --sec-type FUT \
  --exchange CME \
  --currency USD \
  --last-trade-date <VERIFIED_6N_CONTRACT_YYYYMM> \
  --multiplier <VERIFIED_6N_MULTIPLIER> \
  --bar-size '1 min' \
  --duration '7 D' \
  --what-to-show TRADES \
  --output /tmp/ict-engine-6n-eth-rbnz-dairy-risk-reversal-gate1-<stamp>/data/raw/6n_1m.csv
```

Do not proceed to Gate 1 until nonzero `1m` origin rows and shifted
`5m/15m/30m/1h/4h/1d` context rows prove ETH/full retained-session coverage and
the exact product-specific cost model is verified.

## Terminal Decision

decision: `terminalized_no_launch_prep_only_runtime_blocked_cost_unverified`

This packet is useful branch/source preparation only. It is not Gate 1 evidence,
not downstream evidence, and cannot be counted as `trade_usable=true`.
