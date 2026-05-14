# Source Label Other-Market Readback v1

Run ID: `20260511T184856+0800-codex-source-label-other-market-readback-v1`

This readback merges existing source-label and other-market artifacts. It does not fetch raw rows and does not edit the shared Current Cursor.

## Decision

`source_label_other_market_readback_v1=partial_sources_no_full_equivalence`

- Source artifacts read: `6`.
- Public/partial attached source-label slots: `33`.
- Accepted calibrated root factors added: `0`.
- Full other-market/source-label equivalence: `false`.
- Full objective achieved: `false`; `update_goal=false`.

## Rows

| Source | Attached/Overlap | Accepted Gate | Decision | Blocking Reason |
|---|---:|---:|---|---|
| `existing_source_label_attachability` | `14` | `0` | `blocked_existing_packets_do_not_form_full_yfinance_label_panel` | full four-root attached cells=0; unsupported cells=126 |
| `public_source_label_candidate_sweep` | `16` | `0` | `new_accepted_source_label_slots=0` | missing slots=596; public HMM/HF/OHLCV labels rejected as proxy or sidecar |
| `hf_tsie_market_regime_dataset` | `0` | `0` | `blocked_hf_tsie_not_attachable_as_mainregimev2_source_label_panel` | candidate Bull/Bear/Sideways mapping only; Crisis and Manipulation missing; no owner-approved MainRegimeV2 equivalence |
| `crystalbull_qqq_daily_labels` | `3` | `0` | `partial_crystalbull_qqq_daily_source_labels_attached_factor_gate_still_blocked` | QQQ daily Bull/Bear/Sideways only; no Crisis root, no intraday/weekly/monthly crosswalk, factor gate still blocked |
| `external_source_label_candidate_screen` | `0` | `0` | `external_source_label_candidate_screen_v1=no_promotable_source_label_equivalence` | promising but blocked=ahaanverma00/nifty-500-market-and-behavior-regime-dataset,sujinwo/tsie-market-regime-dataset; no promotable MainRegimeV2 equivalence |
| `source_label_equivalence_intake` | `0` | `0` | `source_label_equivalence_intake_verifier_v1=ready_rows_not_acquired` | missing files=2; status=blocked; reason=missing_required_files |

## Readback

- Existing accepted packets and CrystalBull add sparse or daily-only provenance, not a complete other-market/full-cycle panel.
- HF TSIE and other public candidates remain sidecar/candidate mappings unless a source owner supplies an approved MainRegimeV2 crosswalk.
- The external intake verifier is still missing source-owned rows/provenance, so no new confidence gate can be claimed.
- This does not close QQQ/NQ/crypto/FX/rates/commodities equivalence or native sub-hour validation.
