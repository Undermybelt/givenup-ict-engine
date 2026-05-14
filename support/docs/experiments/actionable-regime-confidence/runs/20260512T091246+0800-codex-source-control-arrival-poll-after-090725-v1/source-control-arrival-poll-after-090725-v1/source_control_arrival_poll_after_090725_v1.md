# Source/Control Arrival Poll After 090725 v1

Run id: `20260512T091246+0800-codex-source-control-arrival-poll-after-090725-v1`

Gate result: `source_control_arrival_poll_after_090725_v1=no_new_required_root_no_unlock`

## Scope

Read-only source/control arrival poll after terminal `090725`. This packet checks exact R6/R5/R3 target roots and recent Downloads/Desktop/tmp dropzone candidates modified after `090725`. It does not mutate target roots, approve local files as source/control evidence, send external requests, run verifier, run selected-data AutoQuant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Board A SHA-256 before artifact: `60ef12e136d26f01dbe634f538c9d02a156cb468d447236cb1337e47dbff6ae4`.
- Post-090725 dropzone candidates: `0`.
- Current R6 required package complete: `False`.
- R5 recency required package complete: `False`.
- R3 native-subhour required files present: `True`.
- R3 Crisis label present: `False`.
- R3 native-subhour unlock: `False`.

## Decision

No new owner-approved/source-owned source/control package was accepted by this readback. R6 owner/export and R5 recency roots remain incomplete or absent. R3 native-subhour rows remain non-unlocking because Crisis is absent.

Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T091246+0800-codex-source-control-arrival-poll-after-090725-v1/source-control-arrival-poll-after-090725-v1/source_control_arrival_poll_after_090725_v1.json`
- Target roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T091246+0800-codex-source-control-arrival-poll-after-090725-v1/source-control-arrival-poll-after-090725-v1/source_control_target_roots_after_090725_v1.csv`
- Dropzone candidates CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T091246+0800-codex-source-control-arrival-poll-after-090725-v1/source-control-arrival-poll-after-090725-v1/source_control_dropzone_candidates_after_090725_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T091246+0800-codex-source-control-arrival-poll-after-090725-v1/checks/source_control_arrival_poll_after_090725_v1_assertions.out`

## Next

Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE order-lifecycle export rows with positives and matched normal controls, source-owned post-2026-01-30 R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 native-subhour labels, or explicit same-exhibit `FLIP`-as-control approval before verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or `update_goal`.
