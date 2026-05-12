# Source/Control Arrival Poll After 074700 v1

Run id: `20260512T075009+0800-codex-source-control-arrival-poll-after-074700-v1`

Gate result: `source_control_arrival_poll_after_074700_v1=no_new_required_root_no_unlock`

## Scope

Read-only source/control arrival poll after the `074446` direct Manipulation verifier registration, `074528` Board A audit registration, `074535` Board B selection-gate registration, `074600` codehost count-once correction, and `074700` open-data corrected readback. This poll does not edit the Current Cursor, mutate target roots, approve public metadata, approve TSIE rows, approve the R6 decision package, run split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Board hash before writeback: `d6cbf967aa04a171d3df417ca41b0d5fef3355000a5044c7c435055c8543163e`.
- R6 owner/export target root `/tmp/ict-engine-board-a-r6-owner-export-v1`: absent.
- R5 recency target root `/tmp/ict-engine-source-panel-recency-extension`: absent.
- R3 native-subhour root `/tmp/ict-engine-native-subhour-source-label-intake`: present, but TSIE-derived and non-promoting.
- R3 labels observed: `Bear`, `Bull`, `Sideways`; `Crisis` remains absent.
- Source-label equivalence target path `/tmp/ict-engine-source-label-equivalence-v1`: absent in this poll. Prior source-label equivalence evidence remains non-target/non-promoting.
- R6 approval decision package `/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid`: present but non-approving, with `approval_present=false`, `canonical_merge_allowed_now=false`, and `downstream_rerun_allowed_now=false`.
- `074446` direct Manipulation verifier remains `schema_ready_unscored_non_promoting`, with positive rows `73`, matched negative rows `73`, and matched group count `70`.
- `074528` Board A audit artifact files are present and already registered.
- `074535` Board B selection gate is registered in the Board B markdown and still requires an explicit user selection of exactly one of `HTF`, `MTF`, or `LTF`.
- `074424` and `074447` public route probes remain negative route evidence after their count/corrected-readback sections.

## Decision

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; direct verifier promoting false; split calibration false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Next

Continue source/control acquisition only. Do not run split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.
