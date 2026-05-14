# Dune nft.wash_trades Export-Path Probe

Run id: `20260511T083150+0800-codex-dune-nft-wash-trades-export-probe`

## Decision

- Gate result: `blocked_dune_export_missing_api_key`
- Accepted direct `Manipulation` 95: `false`
- MainRegimeV2 root-label slots added: `0`
- Manipulation label slots added: `0`
- DUNE_API_KEY present: `false`
- Public query-result probe status: `401`

## What the docs establish

- Dune documents `nft.wash_trades` as a curated NFT wash-trading table.
- Required replay columns are present in the documented schema: `block_time`, `block_date`, `tx_hash`, `unique_trade_id`, and `is_wash_trade`.
- Filter provenance columns are documented for same buyer/seller, back-and-forth, repeated trading, common funding wallet, and flashloan filters.
- Dune API documentation requires an API key for authenticated SQL execution; the current shell has no `DUNE_API_KEY`.

## Candidate SQL

```sql
WITH labeled AS (
  SELECT
    blockchain,
    project,
    nft_contract_address,
    token_id,
    buyer,
    seller,
    block_time,
    block_date,
    tx_hash,
    unique_trade_id,
    CAST(is_wash_trade AS BOOLEAN) AS manipulation_positive,
    filter_1_same_buyer_seller,
    filter_2_back_and_forth_trade,
    filter_3_bought_or_sold_3x,
    filter_4_first_funded_by_same_wallet,
    filter_5_flashloan
  FROM nft.wash_trades
  WHERE block_time IS NOT NULL
    AND is_wash_trade IS NOT NULL
),
balanced AS (
  SELECT
    *,
    row_number() OVER (
      PARTITION BY manipulation_positive
      ORDER BY block_time, unique_trade_id
    ) AS class_row_number
  FROM labeled
)
SELECT *
FROM balanced
WHERE class_row_number <= 5000
ORDER BY block_time, unique_trade_id
```

## Result

- No replayable rows were exported in this run.
- No positive/negative chronological calibration/test windows were materialized.
- The table remains a strong candidate source, but it cannot be accepted without authenticated export and calibration.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
