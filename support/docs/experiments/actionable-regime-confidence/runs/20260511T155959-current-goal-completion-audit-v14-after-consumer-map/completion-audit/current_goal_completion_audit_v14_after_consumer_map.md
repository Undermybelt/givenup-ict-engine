# Current Goal Completion Audit v14 After Consumer Map

Run id: `20260511T155959+0800-current-goal-completion-audit-v14-after-consumer-map`.

## Objective Restatement

The requested goal is:

1. Every active regime has a 95% calibrated confidence packet.
2. The regime evidence is validated across other markets.
3. The regime evidence is validated across other timeframes.
4. The result is reported only after the above are covered.

Active Board A taxonomy:

- Price roots: `Bull`, `Bear`, `Sideways`, `Crisis`.
- Separate direct overlay: `Manipulation`.
- Child/sub-regime labels and proxy features do not count as parent roots.

## Completion Decision

- Scoped active-lane 95% status: `accepted_95`.
- Full objective achieved: `false`.
- `update_goal`: `false`.

Reason: `regime_factor_consumer_map_v1` proves a scoped 95% consumer factor exists for `Bull`, `Bear`, `Sideways`, `Crisis`, and scoped direct `Manipulation`, but it explicitly does not close full species/full-cycle coverage, ticker-specific support, 2026 recency, or missing direct `Manipulation` varieties.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status | Notes |
|---|---|---|---|
| Every active lane has a 95% factor | `regime_factor_consumer_map_v1` | pass_scoped | `5/5`: `Bull`, `Bear`, `Sideways`, `Crisis`, `Manipulation`. |
| Price-root regimes are main classes | Board relock + `market_regime_context_packet_v1` | pass | Main roots are exactly `Bull/Bear/Sideways/Crisis`; child labels remain provenance only. |
| Price-root confidence floor >= 0.95 | `market_regime_context_packet_v1` | pass | Floors: `Bull=0.9797225384`, `Bear=0.963920242`, `Sideways=0.9529358324`, `Crisis=0.9619059575`. |
| Direct `Manipulation` has direct evidence | `regime_factor_consumer_map_v1` + direct variety matrix | pass_scoped | Scoped direct overlay floor `0.967945`; no OHLCV proxy promotion. |
| Direct `Manipulation` full species coverage | `regime_factor_consumer_map_v1` | fail | Missing/blocked varieties remain `pump_dump_social_text_or_twitter`, `spoofing_layering_enforcement_cases`, `local_spoofing_repos`, `quote_stuffing`, `pinging`, `bear_raid_or_painting_tape`. |
| Cross-timeframe validation | market context layers | pass_scoped | Daily, `1w`, `1mo`, and exact `1h` context layers exist; native sub-hour source overlap remains blocked. |
| Cross-market/species validation | same-source 39-ticker panel + consumer map | partial | US/source-panel breadth is covered for context; full NQ/QQQ/futures/crypto/FX source-label equivalence is not closed. |
| Ticker-specific support | exact `1h` universe expansion | partial | Strict ticker/root accepted rows remain `41/156`; pooled context is not ticker-specific support. |
| 2026 recency | stock-market-regimes source panel | partial | Source panel ends `2026-01-30`. |
| Completion authority | this audit | fail | Required missing items remain; no `update_goal`. |

## Evidence

- `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T144838-codex-market-regime-context-packet-v1/market-regime-context/market_regime_context_packet_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T141910-codex-exact-1h-source-universe-expansion-v1/exact-1h-universe/exact_1h_source_universe_expansion_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_manifest_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T131311-codex-direct-manipulation-variety-matrix-v1/direct-manipulation/direct_manipulation_variety_matrix_v1.json`

## Next

Use `regime_factor_consumer_map_v1.csv` as the downstream consumer contract. Continue full-objective work only on missing coverage: source-owned spoofing/layering rows with matched controls, missing direct varieties, full species/full-cycle validation, ticker-specific support, and source-panel recency.
