# Board A External Intake Bundle v1

Run ID: `20260511T183606+0800-codex-external-intake-bundle-v1`

This package converts the remaining strict Board A blockers into an executable external intake contract. It does not accept rows, does not move the Current Cursor, and does not make a trade-usable claim.

## Decision

`board_a_external_intake_bundle_v1=ready_for_rows_not_acquired`

- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full objective achieved: `false`; `update_goal=false`.
- Current Cursor edited: `false`.
- Raw provider rows committed: `false`.

## Intake Root

`/tmp/ict-engine-board-a-external-intake-bundle-v1`

## Required Files

| Package | File | Destination | Purpose |
|---|---|---|---|
| `price_root_equivalence` | `source_label_equivalence_rows.csv` | `/tmp/ict-engine-board-a-external-intake-bundle-v1/price-root/source_label_equivalence_rows.csv` | source-owned or owner-approved MainRegimeV2 crosswalk rows for QQQ/NQ/NDX/futures, crypto, FX/rates/commodities |
| `price_root_equivalence` | `source_label_equivalence_provenance.json` | `/tmp/ict-engine-board-a-external-intake-bundle-v1/price-root/source_label_equivalence_provenance.json` | owner, approval, export identity, hashes, source URLs, and non-proxy attestation for price-root equivalence |
| `source_panel_recency_extension` | `source_panel_recency_extension_rows.csv` | `/tmp/ict-engine-board-a-external-intake-bundle-v1/recency/source_panel_recency_extension_rows.csv` | source-owned MainRegimeV2 rows strictly after 2026-01-30 |
| `source_panel_recency_extension` | `source_panel_recency_extension_provenance.json` | `/tmp/ict-engine-board-a-external-intake-bundle-v1/recency/source_panel_recency_extension_provenance.json` | source revision identity proving labels are not provider-only candles or generated future-return labels |
| `direct_manipulation_species` | `direct_manipulation_positive_rows.csv` | `/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_positive_rows.csv` | direct Manipulation positives for missing species: spoofing/layering, quote stuffing, pinging, bear raid, painting tape, social/text pump-dump |
| `direct_manipulation_species` | `direct_manipulation_matched_controls.csv` | `/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_matched_controls.csv` | matched normal controls for every positive event group |
| `direct_manipulation_species` | `direct_manipulation_provenance.json` | `/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_provenance.json` | source owner, row provenance, event taxonomy, matched-negative policy, and hashes |

## Guardrails

- Price-root equivalence must cover `us_index_futures_equivalence`, `crypto_equivalence`, and `fx_rates_commodities_equivalence`.
- MainRegimeV2 labels are limited to `Bull`, `Bear`, `Sideways`, and `Crisis`; every label needs its own qualifying condition and validation context.
- Recency extension rows must be source-owned labels strictly after `2026-01-30`.
- Direct Manipulation positives must have matched normal controls for every positive group.
- Provider-only OHLCV, HMM/generated labels, future-return labels, and unapproved `^IXIC -> QQQ/NQ=F` mapping fail closed.
- Schema readiness is not confidence acceptance; after a verifier pass, rerun unchanged chronological, heldout market/timeframe, BBN, CatBoost, and execution-tree gates.

## Verifier

```bash
python3 docs/experiments/actionable-regime-confidence/runs/20260511T183606-codex-external-intake-bundle-v1/external-intake-bundle/board_a_external_intake_verifier_v1.py --intake-root /tmp/ict-engine-board-a-external-intake-bundle-v1
```

Current missing-intake result:

```json
{
  "missing_files": [
    "/tmp/ict-engine-board-a-external-intake-bundle-v1/price-root/source_label_equivalence_rows.csv",
    "/tmp/ict-engine-board-a-external-intake-bundle-v1/price-root/source_label_equivalence_provenance.json",
    "/tmp/ict-engine-board-a-external-intake-bundle-v1/recency/source_panel_recency_extension_rows.csv",
    "/tmp/ict-engine-board-a-external-intake-bundle-v1/recency/source_panel_recency_extension_provenance.json",
    "/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_positive_rows.csv",
    "/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_matched_controls.csv",
    "/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_provenance.json"
  ],
  "reason": "missing_required_files",
  "status": "blocked"
}
```

## Source Evidence Used

- `20260511T182922-codex-source-label-equivalence-intake-verifier-v1`: existing source-label intake request is executable but missing rows.
- `20260511T183328-codex-external-source-label-candidate-screen-v1`: external candidates remain blocked without owner-approved MainRegimeV2 equivalence.
- `20260511T182601-codex-direct-manipulation-source-scan-v2`: no ready direct species source with positives plus matched negatives.
- `20260511T183018-codex-hf-pumpdump-schema-audit-v1`: pump/dump rows lack explicit labels and matched controls.
