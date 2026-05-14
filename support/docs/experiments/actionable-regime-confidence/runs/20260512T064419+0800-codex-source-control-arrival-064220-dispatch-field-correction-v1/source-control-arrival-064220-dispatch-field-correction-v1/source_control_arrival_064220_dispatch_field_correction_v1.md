# Source/Control Arrival 064220 Dispatch Field Correction v1

Run id: `20260512T064419+0800-codex-source-control-arrival-064220-dispatch-field-correction-v1`

Gate result: `source_control_arrival_064220_dispatch_field_correction_v1=dispatch_sent_field_false_no_unlock`

## Scope

Append-only correction for the `064220` Board A source/control arrival refresh registration. This does not send mail, use a vendor portal, approve TSIE, mutate target roots, run direct verifier, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Evidence

- Source artifact JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1/source-control-arrival-refresh-after-063906-v1/source_control_arrival_refresh_after_063906_v1.json`
- Dispatch assets CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1/source-control-arrival-refresh-after-063906-v1/source_control_arrival_refresh_dispatch_assets_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1/checks/source_control_arrival_refresh_after_063906_v1_assertions.out`

## Correction

The `064220` artifact JSON reports `external_dispatch_sent_evidence=false`, and both dispatch draft rows report `sent_evidence=False`. The board sentence that says `external_dispatch_sent_evidence=true` is stale/incorrect and must not be used as a sent-request, ticket, export, license, order, support, or approval signal.

## Decision

- Valid required unlock: `false`.
- Source/control evidence acquired: `false`.
- Accepted rows added: `0`.
- Canonical merge allowed now: `false`.
- Downstream rerun allowed now: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, verifier-native R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before rerunning direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback.
