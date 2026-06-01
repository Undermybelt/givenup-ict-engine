# Instrument Cost Model Verification

## Rule

Never guess transaction costs for profitability-factor work. Costs are part of
the evidence chain, not a filler default. Verify them for the exact instrument
class, product, market, currency, broker, pricing plan, venue, and historical fee
date before cost-survival, paper/sim, promotion, or trade-usability decisions.

The responsible agent must proactively search the relevant official source when
any field is unknown. Do not wait for the user to supply the fee table, and do
not substitute a nearby product, market, or asset class. Acceptable first sources
are broker fee schedules, exchange fee pages, clearing/regulatory fee pages, and
the account/paper-trade configuration that proves the pricing plan or region.
Blog posts, old run packets, or another agent's prose can only be pointers to
refresh, not proof.

If the cost cannot be verified in the current work slice, write
`cost_model_unverified`, keep `promotion_allowed=false` and
`trade_usable=false`, and stop before downstream promotion.

## What Must Be Checked

For every traded symbol or contract, record:

- Instrument class: stock, ETF, futures, option, perp, spot crypto, FX, CFD, or
  other.
- Market and venue: US stock, HK stock, EU stock, CME, CBOT, COMEX, NYMEX,
  CBOE/OCC, crypto exchange, etc.
- Currency: commission currency, PnL currency, quote currency, and any FX
  conversion or minimum ticket fee.
- Broker/pricing plan: tiered vs fixed, account region, market-data/routing
  assumptions where they change fees.
- Effective date: current schedule for live/paper work, or historical schedule
  if backtesting a period where fees changed.
- Unit convention: per share, percent of trade value, per order, per contract,
  per side, round turn, maker/taker, exercise/assignment, clearing/regulatory,
  exchange pass-through, borrowing/financing, and minimum/maximum caps.
- Symbol mapping: ticker to listed market for stocks/ETFs; futures root to exact
  contract family; option root/expiry/multiplier; ETF product class if fees vary.

## Required Agent Procedure

1. Classify the instrument before backtesting: stock, ETF, futures, option,
   perp, spot crypto, FX, CFD, or other.
2. Resolve the exact tradable product and market: listed exchange/venue for
   stocks and ETFs, futures root and contract family, option class/expiry/
   multiplier, crypto exchange and fee tier, or broker-specific CFD/FX schedule.
3. Resolve currency and unit conventions: commission currency, PnL/quote
   currency, multiplier/tick value, per-share/per-contract/per-order/notional,
   per-side vs round-turn, minimums/caps, and FX conversion where relevant.
4. Search official current sources in the same turn. For historical backtests,
   also check whether the fee schedule changed during the tested period; if the
   historical schedule cannot be proven and the difference can change the
   verdict, mark unverified.
5. Write the source URLs, fetch timestamp, pricing-plan assumption, and all fee
   components into the workdoc, claim pointer, and terminal metrics packet.
6. Convert the verified fee into the backtest engine's units explicitly. If the
   engine only supports bps/notional but the instrument charges per contract or
   per share, record the conversion formula or run a post-processor; do not hide
   it behind a generic `fee` field.
   For `ict-engine` futures scripts, reuse
   `support/scripts/research/instrument_cost_model.py` for root normalization,
   verified IBKR futures profiles, and per-contract USD-to-return conversion.
   Do not create a wrapper-local futures cost table or use hardcoded
   `cost_bps` / `fee=0.0005` as futures commission authority.
7. If any required component remains unknown, set
   `cost_model_status=cost_model_unverified`, `promotion_allowed=false`,
   `trade_usable=false`, and `update_goal=false`.

## Asset-Class Defaults Are Not Proof

- Stocks: many stocks on the same market may share a schedule, but the market,
  currency, minimums, caps, stamp duty/transaction levy, SEC/FINRA fees, and
  broker region still matter. Do not carry a US-stock fee into HK/EU/JP/A-share
  stocks, and do not use a later fee table for an earlier year without noting the
  effective-date assumption.
- ETFs: often look like stocks, but product class, exchange, domicile, currency,
  regulatory fees, stamp/transaction taxes, borrow/financing, and broker routing
  can differ. Verify instead of assuming one ETF equals another.
- Futures: each contract family can have different broker, exchange,
  regulatory, clearing, tick-value, multiplier, spread, and surcharge economics.
  See `futures-contract-cost-models-ibkr.md` for the current IBKR dated table.
- Options: do not infer from stocks. Options can have per-contract commissions,
  exchange fees, OCC/clearing/regulatory fees, assignment/exercise fees,
  premium-based caps/minimums, option class differences, and changing exchange
  schedules.
- Crypto/perps: maker/taker tiers, funding, borrow, settlement, withdrawal,
  stablecoin quote, and VIP volume tiers can dominate. Verify the exact exchange
  schedule and tier used by the backtest or paper account.

## Backtest Packet Fields

Every cost-sensitive run should include:

```text
cost_model_status=verified|cost_model_unverified
cost_model_source_url=<url>
cost_model_fetched_at=<timestamp>
cost_model_effective_for=<live_current|historical_period>
broker=<broker>
account_region=<region or unknown>
pricing_plan=<tiered|fixed|maker_taker|unknown>
instrument_class=<stock|etf|future|option|perp|crypto|...>
market=<market/exchange>
currency=<commission/PnL currency>
symbol_mapping=<exact listed symbol or contract>
unit_convention=<per_share|percent_notional|per_contract|per_order|...>
per_side_or_round_turn=<per_side|round_turn|unknown>
commission=<amount/formula>
exchange_fee=<amount/formula or none>
regulatory_fee=<amount/formula or none>
clearing_fee=<amount/formula or none>
other_fee=<amount/formula or none>
minimum_fee=<amount or none>
maximum_fee=<amount or none>
currency_conversion=<amount/formula or none>
slippage_spread_model=<separate explicit model>
```

## Fail-Closed Examples

- `ES` fee copied onto `NQ`, `YM`, `MES`, or `GC` without verifying the product.
- US equity commission copied onto HK, EU, JP, or A-share symbols.
- Stock commission copied onto ETF or option runs without checking product rules.
- ETF commission copied across US-listed, HK-listed, EU-listed, leveraged,
  inverse, bond, commodity, or hard-to-borrow ETFs without checking venue,
  domicile, borrow/financing, and currency effects.
- Option cost modeled as stock commission only, omitting per-contract,
  exchange/OCC/regulatory, exercise, assignment, or premium cap/minimum fields.
- Current fee schedule applied to a historical backtest period where fees changed
  and the change could affect the verdict.
- Freqtrade/AQ `fee=0.0005` used for a futures or options run without explaining
  the conversion from actual per-contract fees.
- A backtest reports positive gross PnL but omits minimum ticket fees, regulatory
  charges, contract multipliers, tick values, currency conversion, or option
  exercise/assignment costs relevant to the strategy.
