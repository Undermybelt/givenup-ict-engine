# R3 Label Count Settled Readback After 071032 v1

Run id: `20260512T071346+0800-codex-r3-label-count-settled-readback-after-071032-v1`

Gate result: `r3_label_count_settled_readback_after_071032_v1=tsie_quarantined_no_crisis_no_unlock_no_downstream`

## Readback

This packet registers the settled output of peer run `20260512T071032+0800-codex-r3-label-count-readback-after-070434-v1` without mutating the R3 root, canonical intake, or any downstream chain.

Source output:
- `docs/experiments/actionable-regime-confidence/runs/20260512T071032+0800-codex-r3-label-count-readback-after-070434-v1/command-output/r3_main_regime_v2_label_counts_header_aware.tsv`

Header-aware label counts:
- `Bear`: `1,435,764`
- `Bull`: `1,435,055`
- `Sideways`: `2,162,084`
- Data rows: `5,032,903`
- `Crisis`: `0`

## Decision

The physical R3 root is present, but it remains TSIE-derived/quarantined and not Crisis-capable. This does not satisfy verifier-native R3 `MainRegimeV2` requirements, R5 post-`2026-01-30` recency, R6 owner/export controls, source/control approval, canonical merge, or downstream promotion.

Accepted rows added: `0`.
R6 owner/export unlock: `false`.
R5 recency unlock: `false`.
R3 native-subhour unlock: `false`.
Valid required-root unlock: `false`.
Source/control evidence acquired: `false`.
Canonical merge: `false`.
Downstream promotion rerun: `false`.
Strict full objective: `false`.
Trade usable: `false`.
`update_goal=false`.

## Artifacts

- TSV: `r3-label-count-settled-readback-after-071032-v1/r3_label_count_settled_readback_after_071032_v1.tsv`
- JSON: `r3-label-count-settled-readback-after-071032-v1/r3_label_count_settled_readback_after_071032_v1.json`
- Assertions: `checks/r3_label_count_settled_readback_after_071032_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
