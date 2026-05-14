# AIMM-GT Public Direct Source Audit

Run ID: `20260511T110628+0800-codex-aimmgt-public-direct-source-audit`

## Candidate

- Source: `AIMM-GT / AIMM arXiv 2512.16103`
- URL: `https://arxiv.org/abs/2512.16103`
- Code finder checked: `https://www.catalyzex.com/paper/aimm-an-ai-driven-multimodal-framework-for`

## Board Contract

- Active taxonomy: `MainRegimeV2`.
- Parent price roots: `Bull`, `Bear`, `Sideways`, `Crisis`.
- Separate direct class/overlay: `Manipulation`.
- Direct `Manipulation` still requires materialized timestamped positives and same-asset/venue negative controls; OHLCV risk scores or synthetic social features are not enough.

## Assessment

| Check | Result |
|---|---|
| Parent-root label windows | rejected |
| Direct `Manipulation` rows | rejected |
| Public row-level data located | false |
| Accepted parent-root slots added | `0` |
| Accepted direct `Manipulation` rows added | `0` |

The public paper surface describes a small daily equity manipulation benchmark: `33` labeled ticker-days, `3` positives, and `30` controls, with real Yahoo Finance OHLCV but synthetic social features due to Reddit API limitations. That shape is not a `Bull`/`Bear`/`Sideways`/`Crisis` parent-root label panel for the missing full-matrix slots.

It also cannot close broader direct `Manipulation` coverage under the current Board A gate. The positive support is too small, the social side is synthetic rather than directly observed, and this bounded audit did not locate a public row-level CSV/parquet/data URL.

## Decision

- Gate result: `blocked_aimmgt_public_source_schema_small_synthetic_no_row_level_direct_rows`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Do not spend another loop on AIMM-GT unless a row-level data/code release is located. Continue exact `MainRegimeV2` label-window acquisition or direct `Manipulation` sources with materialized positives and same-asset/venue negatives.
