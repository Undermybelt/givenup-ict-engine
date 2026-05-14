# R6 Owner Official Availability Refresh v1

Run id: `20260512T054025-codex-r6-owner-official-availability-refresh-v1`

Gate result: `r6_owner_official_availability_refresh_v1=official_products_rechecked_no_export_rows_no_promotion`

Board hash before artifact: `8cf23812829614c65ff1326ea2eb11913ead851dd5eeee42298dfb088b0601cd`

## Scope

Bounded source-acquisition refresh for the active R6 owner/export blocker after the `052650` v5 dispatch manifest. This run checks current official owner-product surfaces and one public Cboe sample schema. It does not send external email, approve `FLIP` controls, copy rows into `/tmp/ict-engine-board-a-r6-owner-export-v1`, mutate source-label/R5/R3 roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Sources Checked

| Owner | Official surface | Local evidence | Fit for R6 |
|---|---|---|---|
| Cboe DataShop | `https://datashop.cboe.com/mdr-quotes-trades-data` | Page fetched to `/tmp/cboe_mdr_quotes_trades.html`; product says MDR contains all quote updates and trade data captured by Cboe internal systems; VIX availability starts March 2006; delivery is SFTP. | Date-fit for 2011-2013 VIX trade/quote context, but not sufficient order-lifecycle controls by itself. |
| Cboe DataShop | `https://datashop.cboe.com/cfe-futures-trades` | Page fetched to `/tmp/cboe_cfe_futures_trades.html`; sample id `226` downloaded to `/tmp/cfe_futures_trades_sample_226.zip`; sample header includes order ids, buy/sell order datetimes, side-added-liquidity, bid/ask, and cancel flags. | Schema-fit for order-side/order-linkage controls, but official historical availability is March 2018 to present, so it misses the 2011-2013 Oystacher window. |
| Cboe DataShop | `https://datashop.cboe.com/cboe-us-futures-multicast-pitch` | Page fetched to `/tmp/cboe_futures_pitch.html`; product says it is a daily archive of CFE depth-of-book real-time feed with execution information, including Level 1 and Level 2 depth. | Depth/order-book fit, but official historical availability is August 2018 to present, so it is not a direct 2011-2013 unlock. |
| CME Group | `https://www.cmegroup.com/market-data/datamine-historical-data/market-depth.html` | Official DataMine product surface located by web search; local `curl` attempts to CME pages returned HTTP `403` or timed out, so no row/sample file was acquired. | Still an owner/export route, not a local evidence root. Need licensed CME Market Depth/Market by Order export and provenance identifiers. |

## Cboe Sample Schema

Sample file: `/tmp/cfe_futures_trades_sample_226.zip`

Sample sha256: `c66702f13a9b8848bf44553ecfc79fab56aab0f693d6d458efa7c72d95e9f9aa`

Sample size: `1064511` bytes

Archive member: `Cboe_CFE_Trades_RTH_20221101.csv`

Header fields:

```text
trade_datetime,session,symbol_id,symbol,futures_root,is_tas_trade,contract_settlement_date,contract_settlement_price,trade_id,side_added_liquidity,was_canceled,canceled_at_datetime,trade_price,trade_size,bid,ask,off_order_book_type,buy_order_datetime,sell_order_datetime,buy_order_id,sell_order_id,buy_order_num_legs,sell_order_num_legs,buy_order_fill_count,sell_order_fill_count
```

This confirms the modern CFE Futures Trades product has fields useful for matched-order/control analysis. It does not unlock Board A because the product page says historical data is available from March 2018 to present, while the active R6 Oystacher window needs 2011-2013 provenance and broad normal controls.

## Decision

No source/control rows were acquired. The required target root `/tmp/ict-engine-board-a-r6-owner-export-v1` remains absent, and the R5/R3 roots remain absent. The active next action stays unchanged: send or otherwise satisfy the CME and Cboe/CFE owner-export requests, preserving ticket/export/license/order/support identifiers in provenance, or obtain explicit approval for the same-exhibit `FLIP` control exception.

Promotion status remains: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Treat Cboe legacy MDR as date-fit VIX trade/quote context, CFE Futures Trades as schema-fit but post-window order-linkage evidence, CFE Futures Multicast PITCH as post-window depth evidence, and CME DataMine as a licensed owner-export route. Do not rerun the provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain until a valid source/control root or explicit approval unlock exists.
