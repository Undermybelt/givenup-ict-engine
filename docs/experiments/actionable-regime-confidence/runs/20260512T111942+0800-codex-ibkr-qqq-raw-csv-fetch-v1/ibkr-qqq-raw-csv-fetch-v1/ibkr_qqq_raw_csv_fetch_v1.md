# IBKR QQQ Raw CSV Fetch v1

Run id: `20260512T111942+0800-codex-ibkr-qqq-raw-csv-fetch-v1`

Scope: provider raw-row evidence only. This does not count as Board A source/control evidence, selected-history approval, canonical merge input, provider-matrix AQ evidence, downstream promotion evidence, live trade evidence, completion, or `update_goal` authorization.

Evidence:
- Command: `command-output/00_ibkr_qqq_1d_30d_fetch.cmd`
- Stdout: `command-output/00_ibkr_qqq_1d_30d_fetch.out`
- Stderr: `command-output/00_ibkr_qqq_1d_30d_fetch.err`
- Exit marker: `checks/00_ibkr_qqq_1d_30d_fetch.exit`
- Raw CSV: `provider-csv/ibkr_QQQ_1d_30d.csv`

Readback:
- `fetch_external.py ibkr-historical` exited `0`.
- Local IBKR gateway port used: `4002`.
- Contract request: `QQQ`, `STK`, `SMART`, primary exchange `NASDAQ`.
- Bar request: `1 day`, `30 D`, `TRADES`.
- Raw CSV rows: `30` data rows plus header.
- First bar: `2026-03-30T00:00:00+00:00`.
- Last bar: `2026-05-11T00:00:00+00:00`.

Decision:
- This repairs the provider-matrix raw-row gap for an IBKR QQQ daily probe.
- It remains provider-layer evidence only. It is not same-root AQ/provider provenance, not comparable crypto-provider evidence, not source/control unlock, and not downstream promotion.
- Promotion allowed: `false`.
- Trade usable: `false`.
- `update_goal=false`.

Gate:
- `ibkr_qqq_raw_csv_fetch_v1=ibkr_raw_rows_present_provider_layer_only_no_promotion`.

