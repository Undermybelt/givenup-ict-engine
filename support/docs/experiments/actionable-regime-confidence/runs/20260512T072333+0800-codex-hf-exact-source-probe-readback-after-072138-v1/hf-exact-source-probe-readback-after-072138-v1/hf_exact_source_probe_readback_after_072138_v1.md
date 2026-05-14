# HF Exact Source Probe Readback After 072138 v1

Run id: `20260512T072333+0800-codex-hf-exact-source-probe-readback-after-072138-v1`
Source run id: `20260512T072138+0800-codex-hf-r5-r3-exact-source-route-probe-after-071538-v1`

Gate result: `hf_exact_source_probe_readback_after_072138_v1=all_exact_queries_zero_no_r5_r3_unlock_no_downstream`

## Scope

Settled readback of the raw `072138` Hugging Face exact-source probe. This packet reads existing command outputs only; it does not rerun Hugging Face search, mutate target roots, copy rows into canonical inputs, approve proxy labels, run direct verifier, run split calibration, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- Source run present: `True`.
- Queries checked: `6`.
- All query exits zero: `True`.
- All JSON payloads arrays: `True`.
- All result counts zero: `True`.

## Decision

The 072138 Hugging Face exact-source probe is a raw command-output root: every checked JSON payload is an array, every query exited 0, and every exact query returned 0 rows. It therefore supplies no MainRegimeV2 dataset, no source-owned post-2026-01-30 R5 rows, and no verifier-native native-subhour R3 labels.

Accepted rows added `0`, R6 owner/export unlock false, R5 recency unlock false, R3 native-subhour unlock false, valid required-root unlock false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T072333+0800-codex-hf-exact-source-probe-readback-after-072138-v1/hf-exact-source-probe-readback-after-072138-v1/hf_exact_source_probe_readback_after_072138_v1.json`
- Query CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T072333+0800-codex-hf-exact-source-probe-readback-after-072138-v1/hf-exact-source-probe-readback-after-072138-v1/hf_exact_source_probe_readback_after_072138_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T072333+0800-codex-hf-exact-source-probe-readback-after-072138-v1/checks/hf_exact_source_probe_readback_after_072138_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-2026-01-30 R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted cross-timeframe MainRegimeV2 source export.
