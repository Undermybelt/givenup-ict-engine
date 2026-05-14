# A10 Order-Flow Input Audit

Loop ID: `20260510T205717+0800-hermes-a10-order-flow-input-audit`

Purpose: audit whether Board A can build order-flow entropy for `TrendExpansion`, `ExtremeStress`, and `ReversalBrewing` from real tick/order-flow/order-book inputs.

Result: `missing_required_inputs`.

The audit scanned current Board A condition/candidate/A8/A9 artifacts and the durable NQ state used by the current loop. It found no complete market-tape or book input set. The current artifacts are OHLCV/count plus derived regime features. Five files contain `trade_id`, but those are internal strategy records, not market tick tape; they do not include price/size/side, signed volume, bid/ask, spread, or L2 depth.

Files:

- `audit/a10_order_flow_input_audit.py`
- `audit/a10_order_flow_input_audit_report.json`
- `audit/a10_scanned_input_fields.csv`
- `checks/a10_order_flow_input_audit.out`
- `evidence_packet_a10_order_flow_input_audit.json`

Decision: A10 remains blocked. Do not use OHLCV proxy optimism for order-flow entropy; ingest aligned historical tick/trade tape plus bid/ask or L2 depth first.
