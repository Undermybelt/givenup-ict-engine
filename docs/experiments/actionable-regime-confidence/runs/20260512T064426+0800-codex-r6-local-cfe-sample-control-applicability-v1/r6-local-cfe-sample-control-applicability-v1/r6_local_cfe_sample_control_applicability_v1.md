# R6 Local CFE Sample Control Applicability v1

Run id: `20260512T064426+0800-codex-r6-local-cfe-sample-control-applicability-v1`

Gate result: `r6_local_cfe_sample_control_applicability_v1=cfe_sample_schema_context_only_no_controls_no_promotion`

Board sha256 before artifact: `4d5a43c14701aa9ec3de96d704107cd7a3aff009360ded12fbdbb10127f8badb`

## Scope

Read-only applicability audit for local CFE/Cboe sample files after the `063906` objective audit. This does not copy files into the R6 target root, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Local Sample Readback

- Zip present: `True`.
- Zip SHA-256: `c66702f13a9b8848bf44553ecfc79fab56aab0f693d6d458efa7c72d95e9f9aa`.
- Member count: `1`.
- CSV rows: `48599`.
- Date span: `2022-11-01` to `2022-11-01`.
- Futures roots: `IBHY,IBIG,VX,VXM`.
- Symbol count: `20`.
- Has bid/ask: `True`; has buy/sell order ids: `True`.
- Label/control columns: `none`.
- Rejection reasons: `single_day_sample_not_cross_period; no_source_manipulation_or_normal_control_labels; no_explicit_normal_control_column; not_oystacher_2011_2013_control_window; below_board_broad_control_support_floor`.

## Header Readback

| File | Exists | HTTP 200 | Not Authenticated | SHA-256 |
|---|---:|---:|---:|---|
| `/tmp/ict-engine-cboe-futures-market-data-headers.txt` | `True` | `True` | `False` | `c20170b9841335fde9e9afbdfc9ab2f63a1cfcb86c0e43ca58919c8cae954cd7` |
| `/tmp/ict-engine-cboe-oof-headers.txt` | `True` | `True` | `False` | `51eba963c962c530db294e417d2b75733ae0e1cd05bdc8e59564cc5520bc21ca` |
| `/tmp/ict-engine-databento-docs-headers.txt` | `True` | `True` | `False` | `b56d86549a06ac15628d401c27a1150858e23d731551ddea8c8952bb3c5045fd` |
| `/tmp/ict-engine-databento-metadata-range-response.json` | `True` | `False` | `True` | `cfec9feffbcc0dabaa0f92491e3609eeb1e9bc8d17625cd7f043be03b609c812` |

## Decision

The CFE sample has useful order-lifecycle schema context, but it is not accepted R6 owner/export control evidence. It covers a single RTH sample day in `2022`, has no source manipulation/normal-control labels, has no ticket/license/export/support provenance, and does not cover the Oystacher 2011-2013 control window.

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired false, target root mutated false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, verifier-native R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T064426+0800-codex-r6-local-cfe-sample-control-applicability-v1/r6-local-cfe-sample-control-applicability-v1/r6_local_cfe_sample_control_applicability_v1.json`
- Header CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064426+0800-codex-r6-local-cfe-sample-control-applicability-v1/r6-local-cfe-sample-control-applicability-v1/r6_local_cfe_sample_header_readback_v1.csv`
- Member summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064426+0800-codex-r6-local-cfe-sample-control-applicability-v1/r6-local-cfe-sample-control-applicability-v1/r6_local_cfe_sample_member_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T064426+0800-codex-r6-local-cfe-sample-control-applicability-v1/checks/r6_local_cfe_sample_control_applicability_v1_assertions.out`
