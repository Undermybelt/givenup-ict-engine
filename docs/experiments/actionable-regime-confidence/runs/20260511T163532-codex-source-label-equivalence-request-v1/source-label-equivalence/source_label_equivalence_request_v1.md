# Source Label Equivalence Request v1

Run ID: `20260511T163532+0800-codex-source-label-equivalence-request-v1`

This is a compact acquisition/request package. It does not accept new rows, download raw data, relax thresholds, or claim a new confidence gate.

## Decision

- Request state: `ready_to_send_or_fulfill`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full objective achieved: `false`.
- `update_goal`: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

## Why This Exists

The current scoped consumer map and daily stock root denominator are useful, but the older strict full objective still has gaps:

- source-label equivalence across NQ/QQQ/futures/crypto/FX is not closed;
- source recency beyond the stock-market-regimes panel tail is not closed;
- native sub-hour overlap remains blocked until source-owned recency labels exist;
- direct `Manipulation` full species coverage is incomplete.

## Target Packages

| Package | Scope | Required Labels | Acceptance |
|---|---|---|---|
| `price_root_equivalence_us_index_futures` | SPY/QQQ/ES/NQ/MNQ/GSPC/NDX | `MainRegimeV2` Bull/Bear/Sideways/Crisis labels plus owner-approved equivalence policy | Wilson95 LCB `>=0.95` per root across chronological and heldout-market splits; no IXIC-to-NDX proxy promotion |
| `price_root_equivalence_crypto` | BTC/ETH spot or perpetual source-native equivalents | Source-owned Bull/Bear/Sideways/Crisis labels | Same source-owned split and confidence gates as price roots |
| `price_root_equivalence_fx_rates_commodities` | FX/rates/commodities | Source-owned Bull/Bear/Sideways/Crisis labels | No OHLCV-derived label backfill |
| `native_subhour_overlap_after_recency` | Source-panel native sub-hour extension | Source-owned labels after `2026-01-30` plus native provider overlap | Overlap must exist before calibration; no broad sub-hour sweep without labels |
| `direct_manipulation_species_exports` | Missing direct manipulation species | Positive rows, matched normal controls, and provenance | Missing species remain abstain until direct rows pass unchanged gates |

## Required Schema

The request schema is materialized in `source_label_equivalence_request_v1_required_schema.csv`. Critical fields are:

- `source_owner`, `source_report_or_dataset`, `source_pull_date`
- `market_family`, `symbol`, `source_symbol`, `equivalence_policy`
- `timestamp_or_date`, `timeframe`
- `main_regime_v2_label` for price roots
- `direct_label` and `matched_negative_group_id` for direct `Manipulation`
- `split_role`, `source_row_id`, `provenance_hash`

## Guardrails

- Do not use OHLCV-only labels as source labels.
- Do not use HMM/generated/future-return labels as source labels.
- Do not promote `^IXIC` to `^NDX`/`QQQ`/`NQ=F` unless a source owner approves that equivalence.
- Do not treat positive-only enforcement inventories as direct `Manipulation` gates.
- Keep raw exports in `/tmp` or `/private/tmp`; commit only compact manifests/checks/samples.

## Next

Use this package to request or import source-owned labels. After data arrives, rerun the unchanged gates. If no data arrives, keep the strict full objective blocked and continue using `regime_factor_consumer_map_v1.csv` only as the scoped downstream consumer contract.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T163532-codex-source-label-equivalence-request-v1/source-label-equivalence/source_label_equivalence_request_v1.json`
- Targets CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T163532-codex-source-label-equivalence-request-v1/source-label-equivalence/source_label_equivalence_request_v1_targets.csv`
- Required schema CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T163532-codex-source-label-equivalence-request-v1/source-label-equivalence/source_label_equivalence_request_v1_required_schema.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T163532-codex-source-label-equivalence-request-v1/checks/source_label_equivalence_request_v1_assertions.out`
