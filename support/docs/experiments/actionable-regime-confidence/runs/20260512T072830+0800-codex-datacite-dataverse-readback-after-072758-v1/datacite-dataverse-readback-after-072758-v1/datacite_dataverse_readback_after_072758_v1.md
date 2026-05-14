# DataCite / Dataverse Readback After 072758 v1

Run id: `20260512T072830+0800-codex-datacite-dataverse-readback-after-072758-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T072758+0800-codex-datacite-dataverse-source-route-probe-after-072412-v1`

Gate result: `datacite_dataverse_readback_after_072758_v1=no_required_source_control_unlock_no_downstream`

## Scope

Readback of the raw `072758` DataCite and Harvard Dataverse source-route probes. This packet does not rerun web search, mutate R3/R5/R6 target roots, approve DataCite/Dataverse false positives, run direct verifier, run split calibration, run canonical merge, run provider/AutoQuant promotion, run filter/Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree readback, make a trade claim, or call `update_goal`.

## Query Readback

All `12` raw query commands exited `0`.

DataCite:
- `3Red Trading spoofing owner export`: `0` results.
- `direct manipulation positive rows matched controls`: `11` total results, all false positives unrelated to required market/source-control rows.
- `MainRegimeV2`: `0` results.
- `native_subhour_source_label_rows`: `0` results.
- `Oystacher spoofing futures order book dataset`: `0` results.
- `stock_market_regimes_2026_extension`: `0` results.

Harvard Dataverse:
- `3Red Trading spoofing owner export`: false positives such as foreign-trade and ERC-20 trading context.
- `direct manipulation positive rows matched controls`: false positives such as lobbying, statistical matching, biophysics, and image-manipulation datasets.
- `MainRegimeV2`: `0` useful results.
- `native_subhour_source_label_rows`: `0` useful results.
- `Oystacher spoofing futures order book dataset`: false positives such as order-learning experiments and executive/confiscation order datasets.
- `stock_market_regimes_2026_extension`: `0` useful results.

## Decision

No DataCite or Dataverse source/control unlock was acquired. The raw `072758` probe adds source-route negative evidence only: no verifier-native R6 owner/export positives, no matched normal controls, no owner/export provenance, no source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, and no verifier-native Crisis-capable R3 native-subhour labels.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- Source command output root: `docs/experiments/actionable-regime-confidence/runs/20260512T072758+0800-codex-datacite-dataverse-source-route-probe-after-072412-v1/command-output/`
- Readback CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T072830+0800-codex-datacite-dataverse-readback-after-072758-v1/datacite-dataverse-readback-after-072758-v1/datacite_dataverse_readback_after_072758_v1.csv`
- JSON summary: `docs/experiments/actionable-regime-confidence/runs/20260512T072830+0800-codex-datacite-dataverse-readback-after-072758-v1/datacite-dataverse-readback-after-072758-v1/datacite_dataverse_readback_after_072758_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T072830+0800-codex-datacite-dataverse-readback-after-072758-v1/checks/datacite_dataverse_readback_after_072758_v1_assertions.out`
