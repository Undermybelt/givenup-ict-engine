# Mendeley Anomaly Order-Lifecycle Audit

Run ID: `20260511T105359+0800-codex-mendeley-anomaly-order-lifecycle-audit`

Board cursor readback: `20260511T103333+0800-codex-mainregimev2-board-a-top-relock`

## Source

- Dataset: `Anomaly bias Stock Trades and Order Dataset`
- Mendeley id: `fsn6fn7ht8`
- DOI: `10.17632/fsn6fn7ht8.1`
- URL: `https://data.mendeley.com/datasets/fsn6fn7ht8/1`
- Zip SHA-256: `406f34f004a68328a6048c38ae0cab37e2283cc6f6943fa98658aab9dd3775da`
- Raw download location: `/tmp/ict-regime-mendeley-anomaly-bias/Stock_Trades_Orders.zip`

## Inspected Files

| File | Lines Including Header | Size Bytes | Useful Fields |
|---|---:|---:|---|
| `Orders .csv` | 602474 | 52921622 | `order_id`, `order_time`, `order_date`, `scrip_code`, `member_code`, `client_id`, `buy_OR_sell`, `RATE`, `QUANTITY`, `AVAILABLE_QUANTITY`, `TRADER_ID`, `TERMINAL_ID`, `LOCATION_ID` |
| `Trades .csv` | 414958 | 56704737 | `TRADE_NUMBER`, `TRADE_TIME`, `TRADE_DATE`, `SCRIP_CODE`, buy/sell member/client/order/trader/location ids, `TRADE_QUANTITY`, `TRADE_RATE`, `TRADE_VALUE` |

## Decision

The source is a real order/trade lifecycle dataset and is relevant as a possible future direct-input candidate. It is not accepted for `Manipulation` because the inspected files do not expose row-level positive/negative manipulation labels, spoofing/layering labels, wash/self-trade labels, or adjudicated event windows.

Gate result: `blocked_mendeley_anomaly_order_lifecycle_unlabeled_no_positive_negative_manipulation_rows`.

- Accepted direct `Manipulation` rows added: `0`.
- Accepted parent-root slots added: `0`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

Next action: find an accompanying adjudicated label file/event list for this dataset, or move on to another direct `Manipulation` source with timestamped positives and same-asset/venue negatives.
