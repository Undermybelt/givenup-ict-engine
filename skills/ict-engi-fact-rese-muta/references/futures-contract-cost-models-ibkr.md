# Futures Contract Cost Models, IBKR, 2026-05-29

## Rule

Futures cost is not a universal `bps` or notional percentage. Model it per
contract and per product: broker execution commission plus exchange fee recovery,
regulatory fee, clearing fee where applicable, and any product/account surcharge.

Before a futures Gate 1, AQ replay, paper/sim validation, or terminal readback:

- Identify the exact tradable contract family (`ES` vs `MES`, `NQ` vs `MNQ`,
  `GC` vs `MGC`, etc.), exchange, currency, multiplier, and tick value.
- Record the source URL, fetch date, account/pricing assumption, and whether the
  amount is per side or round turn.
- Compute trade cost as `contracts * (entry_cost_per_contract + exit_cost_per_contract)`.
- Treat unknown fees, unknown contract mapping, unknown multiplier/tick value, or
  ambiguous side convention as `cost_model_unverified` and fail closed.
- Do not substitute `5bps/side` as the futures commission model. Bps/notional may
  be kept only as an explicit slippage/stress scenario separate from commission.
- In `ict-engine`, the canonical code owner is
  `support/scripts/research/instrument_cost_model.py`. Futures wrappers should
  import that helper for cost profiles and conversion instead of copying a local
  `FUTURES_COST_PROFILES` table. The helper's `GATE1_STRESS_BPS_PER_SIDE` is
  stress telemetry, not commission authority.

## IBKR Tiered Non-Member Reference

Observed from IBKR public pages on 2026-05-29:

- Main futures commissions: `https://www.interactivebrokers.com/en/pricing/commissions-futures.php`
- CME fee recovery: `https://www.interactivebrokers.com/en/accounts/fees/CME.php`
- CBOT fee recovery: `https://www.interactivebrokers.com/en/accounts/fees/CBOT.php`
- COMEX fee recovery: `https://www.interactivebrokers.com/en/accounts/fees/COMEX.php`

The IBKR main page says low-volume US futures execution commission is `USD
0.85/contract` for standard futures and `USD 0.25/contract` for the
Spot-Quoted/E-micro group. The page's own ES example states:

`1 ES Futures Contract = IBKR Execution Fee USD 0.85 + Exchange Fee USD 1.38 + Clearing Fee USD 0.00 + Regulatory Fee USD 0.02 = USD 2.25`

The exchange-fee pages state that rates generally reflect non-member exchange
rates, that regulatory fees are NFA-assessed, and that give-up surcharge is
waived when IBKR is both prime and executing broker.

## Working Table

Use this as a dated starting point only; refresh sources before a new live or
paper/sim decision.

| Product | Source group | IBKR exec | Exchange fee recovery | Regulatory | Estimated all-in per side | Round turn |
|---|---:|---:|---:|---:|---:|---:|
| `ES` | CME E-mini S&P | `0.85` | `1.38` | `0.02` | `2.25` | `4.50` |
| `NQ` | CME E-mini Equity | `0.85` | `1.38` | `0.02` | `2.25` | `4.50` |
| `YM` | CBOT Mini-sized Dow | `0.85` | `1.38` | `0.02` | `2.25` | `4.50` |
| `MES` | CME Micro E-mini | `0.25` | `0.35` | `0.02` | `0.62` | `1.24` |
| `MNQ` | CME Micro E-mini | `0.25` | `0.35` | `0.02` | `0.62` | `1.24` |
| `M2K` | CME Micro E-mini | `0.25` | `0.35` | `0.02` | `0.62` | `1.24` |
| `MYM` | CBOT Micro E-mini | `0.25` | `0.35` | `0.02` | `0.62` | `1.24` |
| `GC` | COMEX Gold | `0.85` | `1.65` | `0.02` | `2.52` | `5.04` |
| `SI` | COMEX Silver | `0.85` | `1.65` | `0.02` | `2.52` | `5.04` |
| `HG` | COMEX Copper | `0.85` | `1.65` | `0.02` | `2.52` | `5.04` |
| `MGC` | COMEX Micro Gold | `0.25` | `0.70` | `0.02` | `0.97` | `1.94` |
| `ZS` | CBOT Ags-Electronic Soybean | `0.85` | `2.15` | `0.02` | `3.02` | `6.04` |
| `ZC` | CBOT Ags-Electronic Corn | `0.85` | `2.15` | `0.02` | `3.02` | `6.04` |
| `LE` | CME Agricultural & Weather Live Cattle | `0.85` | `2.10` | `0.02` | `2.97` | `5.94` |
| `BRE` | CME Foreign Exchange Brazilian Real | `0.85` | `1.60` | `0.02` | `2.47` | `4.94` |
| `ZF` | CBOT 5-Year U.S. Treasury Note | `0.85` | `0.65` | `0.02` | `1.52` | `3.04` |
| `ZN` | CBOT 10-Year U.S. Treasury Note | `0.85` | `0.80` | `0.02` | `1.67` | `3.34` |
| `ZB` | CBOT U.S. Treasury Bond | `0.85` | `0.87` | `0.02` | `1.74` | `3.48` |

Notes:

- This assumes IBKR tiered, low monthly volume, non-member rates, USD products,
  and no give-up surcharge. Different account status, memberships, exchange
  incentive programs, regions, routing, or fee changes can alter the result.
- If the test uses TOMAC symbols like `XAU`, map them to the actual futures
  contract (`GC`, `MGC`, or another product) before applying costs. If the map is
  not proven, classify the lane as `cost_model_unverified`.
- For MGC, the 2026-05-30 MGC Kalman VWAP slope reclaim run used IBKR's
  Products & Exchanges chain as broker-side contract-spec proof: product search
  mapped `MGC` to E-Micro Gold COMEX underlying conid `79702479`,
  contract-details returned FUT conid `712565978`, and `trsrv/secdef` confirmed
  `assetClass=FUT`, `ticker=MGC`, `listingExchange=COMEX`, `expiry=20260626`,
  `multiplier=10.0`, and tick increment `0.1`, implying `tick_value_usd=1.0`.
  With IBKR E-micro commission `0.25`, COMEX exchange fee recovery `0.70`, and
  regulatory recovery `0.02`, the ordinary outright all-in cost was `0.97` per
  side and `1.94` round turn. A COMEX carrying-fee column of `0.20` was observed
  but not counted for ordinary outright backtest cost.
- For Micro E-mini index futures `MES` and `MNQ`, the 2026-05-30 MES/MNQ/MGC
  opening VWAP RVOL reclaim cost-model hardening used IBKR public fee pages and
  the Products & Exchanges chain as broker-side contract-spec proof. IBKR
  product search mapped `MES` to Micro E-Mini S&P 500 Stock Price Index CME
  underlying conid `362673777` and `MNQ` to Micro E-Mini Nasdaq-100 Index CME
  underlying conid `362687422`; contract-details returned listed FUT conids;
  `trsrv/secdef` confirmed `assetClass=FUT`, `ticker=MES|MNQ`,
  `listingExchange=CME`, `currency=USD`, `expiry=20260618`, `multiplier=5.0`
  for MES, `multiplier=2.0` for MNQ, and tick increment `0.25`, implying
  `tick_value_usd=1.25` for MES and `tick_value_usd=0.50` for MNQ. The same
  packet refreshed IBKR's E-micro commission group (`MES, MNQ, MGC`) at `0.25`
  per contract, CME Micro E-mini exchange fee recovery `0.35`, and regulatory
  recovery `0.02`, so the working all-in IBKR ordinary outright model is
  `MES=0.62` per side / `1.24` round turn and `MNQ=0.62` per side / `1.24`
  round turn before separate slippage/spread. Keep exact contract-month mapping
  and fee-date source readback in the runtime packet.
- For Treasury futures such as `ZN`, preserve the CBOT fee row by exact product
  group. The 2026-05-30 ZN source reserve used IBKR's `ZN, TN` U.S. Treasury
  Futures fee-recovery row (`0.80` non-member), the all-product regulatory row
  (`0.02`), and IBKR broker-side FUT secdef rows with `multiplier=1000.0` and
  tick increment `0.015625`, implying `tick_value_usd=15.625`.
- For Treasury futures such as `ZF`, preserve the CBOT fee row by exact product
  group. The 2026-05-30 ZF source/prep packet used IBKR's `ZF` U.S. Treasury
  Futures fee-recovery row (`0.65` non-member), the all-product regulatory row
  (`0.02`), and IBKR broker-side FUT secdef rows with `multiplier=1000.0` and
  tick increment `0.0078125`, implying `tick_value_usd=7.8125`.
- For Treasury futures such as `ZB`, preserve the CBOT fee row by exact product
  group. The 2026-05-30 ZB source reserve used IBKR's `ZB, TWE` U.S. Treasury
  Futures fee-recovery row (`0.87` non-member), the all-product regulatory row
  (`0.02`), and IBKR broker-side FUT secdef rows with `multiplier=1000.0` and
  tick increment `0.03125`, implying `tick_value_usd=31.25`.
- For `YM`, the 2026-05-30 official-source refresh used IBKR public product
  search plus broker-side FUT secdef after CME contract-spec HTML failed from
  the host. IBKR returned `assetClass=FUT`, `ticker=YM`,
  `listingExchange=CBOT`, `currency=USD`, `multiplier=5.0`, and tick increment
  `1.0` for listed YM futures months, implying `tick_value_usd=5.0`. The same
  packet verified IBKR low-volume USD futures commission `0.85`, CBOT `YM`
  exchange fee recovery `1.38`, and regulatory fee recovery `0.02`, so the
  working all-in IBKR YM model is `2.25` per side and `4.50` round turn before
  separate slippage/spread. Keep exact continuous-symbol to contract-month
  mapping in the runtime packet.
- For COMEX Copper `HG`, the 2026-05-30 source-only refresh used IBKR public
  product search plus broker-side FUT secdef after the direct CME Copper
  contract-spec HTML failed from the host. IBKR mapped `HG` to Copper Index
  COMEX underlying conid `36557087`, returned 49 HG FUT conids via
  `contract-details`, and `trsrv/secdef` returned matching `assetClass=FUT`,
  `ticker=HG`, `listingExchange=COMEX`, `currency=USD`, `multiplier=25000.0`,
  and tick increment `0.00050`, implying `tick_value_usd=12.5`. The same packet
  verified IBKR low-volume USD futures commission `0.85`, COMEX `GC, HG, SI`
  exchange fee recovery `1.65`, and regulatory fee recovery `0.02`, so the
  working all-in IBKR HG ordinary outright model is `2.52` per side and `5.04`
  round turn before separate slippage/spread. Keep exact continuous-symbol to
  contract-month mapping, roll handling, and historical fee-date assumptions in
  the runtime packet.
- For CBOT Soybean futures `ZS`, the 2026-05-30 source-only refresh used IBKR
  public product search plus broker-side FUT secdef after the direct CME/CBOT
  soybean contract-spec HTML failed from the host. IBKR mapped `ZS` to Soybean
  Futures - CBOT underlying conid `11160664`, returned 20 ZS FUT conids via
  `contract-details`, and `trsrv/secdef` returned matching `assetClass=FUT`,
  `ticker=ZS`, `listingExchange=CBOT`, `currency=USD`, `multiplier=5000.0`,
  and tick increment `0.0025`, implying `tick_value_usd=12.5`. The same packet
  verified IBKR low-volume USD futures commission `0.85`, CBOT
  `Ags-Electronic Futures ZC, ZL, ZM, ZO, ZR, ZS, ZW, KE` non-member exchange
  fee recovery `2.15`, and regulatory fee recovery `0.02`, so the working
  all-in IBKR ZS ordinary outright model is `3.02` per side and `6.04` round
  turn before separate slippage/spread. Keep exact continuous-symbol to
  contract-month mapping, crop-roll handling, sidecar timestamp provenance, and
  historical fee-date assumptions in the runtime packet.
- For CBOT Corn futures `ZC`, the 2026-05-30 source-only refresh used IBKR
  public product search plus broker-side FUT secdef after the direct CME/CBOT
  corn contract-spec HTML failed from the host. IBKR mapped `ZC` to Corn
  Futures - CBOT underlying conid `11160400`, returned 15 ZC FUT conids via
  `contract-details`, and `trsrv/secdef` returned matching `assetClass=FUT`,
  `ticker=ZC`, `listingExchange=CBOT`, `currency=USD`, `multiplier=5000.0`,
  and tick increment `0.0025`, implying `tick_value_usd=12.5`. The same packet
  verified IBKR low-volume USD futures commission `0.85`, CBOT
  `Ags-Electronic Futures ZC, ZL, ZM, ZO, ZR, ZS, ZW, KE` non-member exchange
  fee recovery `2.15`, and regulatory fee recovery `0.02`, so the working
  all-in IBKR ZC ordinary outright model is `3.02` per side and `6.04` round
  turn before separate slippage/spread. Keep exact contract-month mapping,
  crop-calendar/ethanol sidecar provenance, term-structure source provenance,
  and historical fee-date assumptions in the runtime packet.
- For CME Live Cattle futures `LE`, the 2026-05-30 ETH/full-session source-only
  refresh used IBKR public product search plus broker-side FUT secdef after the
  direct CME Live Cattle contract-spec HTML failed from the host. IBKR mapped
  `LE` to Live Cattle - CME underlying conid `33221066`, returned listed FUT
  conids via `contract-details`, and `trsrv/secdef` returned matching
  `assetClass=FUT`, `ticker=LE`, `listingExchange=CME`, `currency=USD`,
  `multiplier=40000.0`, and tick increment `0.00025`, implying
  `tick_value_usd=10.0`. The same packet verified IBKR low-volume USD futures
  commission `0.85`, CME Agricultural & Weather Product futures fee recovery
  `2.10` for the row containing `LE`, and regulatory fee recovery `0.02`, so
  the working all-in IBKR ordinary direct-execution model is `2.97` per side
  and `5.94` round turn before separate slippage/spread. A separate IBKR
  give-up surcharge row of `0.05` exists; include it only if the actual route is
  give-up rather than ordinary direct IBKR execution. Keep exact contract-month
  mapping, all-session row coverage, cattle inventory/feed-grain sidecar
  provenance, and historical fee-date assumptions in the runtime packet.
- For COMEX Gold `GC` and E-Micro Gold `MGC`, the 2026-05-30 XAU tailshock
  source-only refresh used IBKR public product search plus broker-side FUT
  secdef after direct CME Gold and E-Micro Gold contract-spec HTML failed from
  the host with TLS EOF. IBKR mapped `GC` to Gold COMEX underlying conid
  `17340718` and `MGC` to E-Micro Gold COMEX underlying conid `79702479`; the
  listed FUT secdef rows returned `assetClass=FUT`, `listingExchange=COMEX`,
  `currency=USD`, `ticker=GC|MGC`, `multiplier=100.0` for GC, `multiplier=10.0`
  for MGC, and tick increment `0.1`, implying `tick_value_usd=10.0` for GC and
  `tick_value_usd=1.0` for MGC. The same packet verified IBKR low-volume USD
  futures commission `0.85` for standard GC, E-micro commission `0.25` for MGC,
  COMEX fee recovery `1.65` for GC/HG/SI, COMEX fee recovery `0.70` for MGC,
  and regulatory fee recovery `0.02`, so the working all-in IBKR ordinary
  outright model is `GC=2.52` per side / `5.04` round turn and `MGC=0.97` per
  side / `1.94` round turn before separate slippage/spread. A continuous TOMAC
  `XAU` cache must still be mapped to exact `GC` or `MGC` contract months and
  roll rules before declaring real-cost survival.
- For CME Brazilian Real futures, use `BRE` as the broker/exchange futures
  ticker rather than a guessed `6L` symbol. The 2026-05-30 BRL source-cost
  reserve used IBKR public Products & Exchanges after direct CME contract-spec
  pages failed from the host with TLS errors. IBKR search for `BRE` returned
  `Brazilian Real in US Dollars - CME` and a `BRL`/CME FUT section; futures
  contract-details returned listed FUT conids; `trsrv/secdef` confirmed
  `assetClass=FUT`, `ticker=BRE`, `listingExchange=CME`, `currency=USD`,
  `multiplier=100000.0`, and tick increment `0.000050`, implying
  `tick_value_usd=5.0`. The same packet verified IBKR low-volume USD futures
  commission `0.85`, CME Foreign Exchange Product fee recovery `1.60` for the
  row containing `BRE`, and regulatory fee recovery `0.02`, so the working
  all-in IBKR ordinary outright model is `BRE=2.47` per side / `4.94` round
  turn before separate slippage/spread. Keep exact contract-month mapping,
  retained-session row coverage, Selic/Fed source timestamp alignment, and
  historical fee-date assumptions in the runtime packet.
- For spread orders, overnight positions, delivery, data, financing, and other
  non-standard cases, re-check product-specific fee notes; do not reuse the
  simple outright table.

## Backtest Reporting Template

Every futures run should include these fields in the workdoc, claim, and terminal
packet when costs affect decisions:

```text
cost_model_status=verified|cost_model_unverified
cost_model_source_url=<url>
cost_model_fetched_at=<local timestamp>
broker=IBKR
pricing_plan=tiered|fixed|unknown
account_fee_assumption=non_member_low_volume|member|unknown
contract_symbol=<ES|MES|NQ|MNQ|GC|MGC|...>
contract_multiplier=<number or unknown>
tick_size=<number or unknown>
tick_value=<number or unknown>
commission_per_contract_per_side=<amount>
exchange_fee_per_contract_per_side=<amount>
regulatory_fee_per_contract_per_side=<amount>
other_fee_per_contract_per_side=<amount or 0 with note>
all_in_per_contract_per_side=<amount>
all_in_round_turn_per_contract=<amount>
slippage_model=<separate explicit model>
```

If any required economic field is unknown, do not declare cost survival,
promotion, paper readiness, trade usability, or goal completion.

## Downstream Readback Contract

Futures downstream/readback gates must use a verified real-cost survivor, not a
blanket `5bps/side` stress survivor. `5bps/side` may remain in artifacts as
stress telemetry, but it is not the futures hard gate when a verified
per-contract instrument-cost row exists.

For futures rows, a downstream cost survivor can be admitted when all of these
are true:

- `trade_count > 0`.
- `survives_instrument_cost=true` or `instrument_cost_total_profit_pct > 0`.
- The row is tied to a futures product by `asset_class=futures`, `sec_type=FUT`,
  a known futures root such as `NQ`, `MNQ`, `ES`, `YM`, `GC`, `MGC`, `ZN`, etc.,
  or a futures/exchange `cost_profile_id`.
- The cost profile is verified and not `unknown`, `missing`, `unverified`, or
  `cost_model_unverified`. Legacy packets may also declare
  `cost_gate_authority=instrument_cost` plus a matching
  `survivors_instrument_cost` label, but this is compatibility evidence only;
  new packets should include the exact verified `cost_profile_id`.

Consumer/readback code should expose both stress and real-cost lists, for
example `exact_5bps_survivors` as telemetry and `exact_real_cost_survivors` or
`survivors.real_cost` as the admission list. A 2bps-only row with no verified
instrument-cost survivor is still invalid. A high-frequency churn row with gross
edge below real commission/spread/slippage remains invalid even if the old
`10bps` stress was too harsh.

## IBKR Product Search Contract-Spec Fallback

When CME contract-spec pages are unavailable but the broker/cost model is IBKR,
IBKR's public Products & Exchanges frontend can provide official broker-side
contract specification evidence. Use the same API chain the frontend uses and
save the JSON responses in the run root:

1. Search the product:

   ```text
   GET https://www.interactivebrokers.com/portal.proxy/v1/mkt/iserver/secdef/search?symbol=<ROOT>
   ```

   For roots such as `MNQ`, this may return the underlying index row
   (`secType=IND`) plus `sections` listing available `FUT` months. The underlying
   row is not enough for futures economics; its multiplier may be `0.0`.

2. Resolve futures contract conids from the underlying conid:

   ```text
   POST https://www.interactivebrokers.com/webrest/search/contract-details
   Content-Type: application/json

   {"productType":"FUT","underConid":"<underlying_conid>"}
   ```

3. Fetch secdef rows for the returned futures conids:

   ```text
   GET https://www.interactivebrokers.com/portal.proxy/v1/mkt/trsrv/secdef?conids=<comma_separated_fut_conids>
   ```

4. Use only rows where `assetClass=FUT`, `ticker=<ROOT>`, and the listing or
   underlying exchange matches the intended venue. Record `currency`,
   `listingExchange`, `expiry`, `multiplier`, and the first `incrementRules[].increment`.
   Compute `tick_value = multiplier * increment` and label the source as an IBKR
   broker-side contract-spec proof, not CME exchange proof.

Fail closed if the chain returns only the underlying `IND`/index row, if the FUT
contract rows omit `multiplier` or tick increment, or if the selected conids do
not match the intended root/exchange/expiry family. Direct CME contract specs are
still preferred when available; this fallback is acceptable for an IBKR-specific
cost model because the broker is the fee and contract-routing authority.
