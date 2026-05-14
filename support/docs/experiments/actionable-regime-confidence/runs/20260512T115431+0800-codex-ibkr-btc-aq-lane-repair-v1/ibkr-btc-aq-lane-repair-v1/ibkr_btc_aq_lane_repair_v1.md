# IBKR BTC AQ Lane Repair v1

Run id: `20260512T115431+0800-codex-ibkr-btc-aq-lane-repair-v1`
Source AQ root: `20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1`

## Scope
Narrow repair attempt for the IBKR BTC/PAXOS lane that blocked the repaired provider-matrix AQ packet.
This run is additive, does not edit ict-engine runtime code, and does not promote any branch.

## Fetch Attempts
- `AGGTRADES` `30 D` `1 hour`: connected `True`, qualified `True`, rows `782`, error ``.
- `AGGTRADES` `60 D` `1 hour`: connected `True`, qualified `True`, rows `1580`, error ``.
- `MIDPOINT` `30 D` `1 hour`: connected `True`, qualified `True`, rows `782`, error ``.
- `MIDPOINT` `60 D` `1 hour`: connected `True`, qualified `True`, rows `1580`, error ``.

## AQ Result
- `ibkr_paxos_1h_repair`: rows `782`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `0.08`, win_rate_pct `38.23529411764706`, profit_factor `1.0144516414659697`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `1.31`, win_rate_pct `52.94117647058824`, profit_factor `1.6850347091222428`.

## Decision
- Gate result: `ibkr_btc_aq_lane_repaired_nonpromoting`.
- Startup floor met: `True`.
- IBKR AQ lane repaired: `True`.
- Mature rooted branch observations added: `51`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
