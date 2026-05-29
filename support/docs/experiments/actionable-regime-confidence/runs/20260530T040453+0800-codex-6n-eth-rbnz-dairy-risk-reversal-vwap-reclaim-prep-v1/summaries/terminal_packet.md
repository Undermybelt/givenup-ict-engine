# 6N ETH RBNZ/Dairy Risk Reversal Terminal Packet

created_at: 2026-05-30T04:04:53+0800
agent_name: codex-6n-eth-rbnz-dairy-risk-reversal-vwap-reclaim-prep
factor_id: 6n_eth_rbnz_dairy_risk_reversal_vwap_reclaim_v1
status: terminalized_no_launch_prep_only_runtime_blocked

## Branch

CommodityFXRiskTransition -> RbnzDairyRiskReversal -> AsiaLondonLiquidityStopRun -> VwapReclaimAfterDairyPolicyShock -> AtrRiskManagedMtfContinuation -> 6n_eth_rbnz_dairy_risk_reversal_vwap_reclaim_v1

session_scope: ETH/full_retained_session
rth_filter_applied: false
origin_timeframe: 1m
context_ladder: 5m/15m/30m/1h/4h/1d

## Evidence

- Workdoc: `/tmp/ict-engine-6n-eth-rbnz-dairy-risk-reversal-vwap-reclaim-prep-20260530T040453+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T040453+0800-codex-6n-eth-rbnz-dairy-risk-reversal-vwap-reclaim-prep.claim`
- Source/cost JSON: `/tmp/ict-engine-6n-eth-rbnz-dairy-risk-reversal-vwap-reclaim-prep-20260530T040453+0800/source_evidence/source_cost_readback_20260530T040453+0800.json`

## Decision

The packet is no-launch because compact audit showed a foreign live factor root:

`/tmp/ict-engine-eur-eth-donchian-tsmom-volcarry-prep-20260530T005133+0800`

IBKR futures commission source was reachable, but CME 6N contract-spec evidence
and RBNZ policy source were not fully reachable from this host. Cost model and
contract spec remain unverified.

provider_rows: not requested
AutoQuant: not launched
Pre-Bayes/BBN/path-ranker/execution-tree: not launched
paper/sim/live: not launched
gate1_verdict: no_verdict

promotion_allowed: false
trade_usable: false
update_goal: false
same_tree_practical_closure: null
