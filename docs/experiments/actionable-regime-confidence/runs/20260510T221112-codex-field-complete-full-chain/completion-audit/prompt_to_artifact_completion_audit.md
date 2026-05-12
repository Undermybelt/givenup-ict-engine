# Prompt To Artifact Completion Audit

Date: 2026-05-10

Objective:
`docs/plans/2026-05-10-actionable-regime-confidence-todo.md` - verify every required regime reaches calibrated confidence at or above 95% before reporting results.

## Completion Criteria

| Requirement | Evidence | Status |
|---|---|---|
| Every required Board A regime has its own accepted packet | `field_complete_full_chain_completion_audit.json` lists six required packets: `SessionLiquidityCoreViable`, `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, and `ThinLiquidity` | pass |
| Every packet is calibrated at 95%+ confidence | `field_complete_full_chain_completion_audit.json` reports min Wilson95 lower confidence bound `0.9536435698638122`; all six packets have `confidence_lane: 95` | pass |
| Each regime keeps its own qualifying condition | `required_regime_packets[].qualifying_condition` is populated for all six regimes; no regime is collapsed into `SessionLiquidityCoreViable` | pass |
| Chronological support and calibration gates are present | Each packet records calibration support, test support, ECE, validation instruments, and validation market contexts; source assertion bundle records contract checks | pass |
| The authoritative Board A markdown reports the current per-regime results | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` points to `20260510T221112-codex-field-complete-full-chain` and its per-regime table records all six 95%+ Wilson values | pass |
| Full-chain consumption was tested without claiming trade usability | `full_chain_evidence` maps Auto-Quant import, Pre-Bayes/filter, BBN apply, CatBoost path-ranker, and execution tree readbacks; verdict keeps `trade_usable: false` and `execution_promotion: blocked` | pass |
| Open downstream work is not misreported as regime-confidence failure | Board A `Next` retains the Board B edge-gate item because trade-usable promotion still needs selected historical data, non-observe execution, and CatBoost structural validation; this is downstream of the user's 95% regime-confidence objective | pass |

## Verified Regime Results

| Regime | Wilson95 LCB | Cal Support | Test Support | ECE |
|---|---:|---:|---:|---:|
| `SessionLiquidityCoreViable` | 0.998989 | 3496 | 3797 | 0.000000 |
| `TrendExpansion` | 0.953644 | 273 | 581 | 0.036674 |
| `RangeConsolidation` | 0.956760 | 503 | 266 | 0.046809 |
| `ExtremeStress` | 0.974129 | 445 | 215 | 0.015574 |
| `ReversalBrewing` | 0.991943 | 843 | 901 | 0.001339 |
| `ThinLiquidity` | 0.985604 | 584 | 263 | 0.001712 |

## Verification Commands

```sh
jq -e '
  (.verdict.board_a_confidence_coverage == "accepted_95_field_complete_6_of_6")
  and (.verdict.accepted_regime_count == 6)
  and (.verdict.accepted_regime_count_required == 6)
  and (.verdict.min_precision_wilson_lcb >= 0.95)
  and (.verdict.trade_usable == false)
  and (.verdict.execution_promotion == "blocked")
  and ([.required_regime_packets[].regime] | sort == ["ExtremeStress","RangeConsolidation","ReversalBrewing","SessionLiquidityCoreViable","ThinLiquidity","TrendExpansion"])
  and all(.required_regime_packets[];
    (.confidence_lane == "95")
    and (.test_precision_wilson_lcb_95 >= 0.95)
    and (.calibration_support >= 120)
    and (.test_support >= 60)
    and (.ece <= 0.05)
    and (.validation_instruments|length >= 2)
    and (.validation_market_contexts|length >= 2)
    and (.qualifying_condition|length > 0)
  )
' docs/experiments/actionable-regime-confidence/runs/20260510T221112-codex-field-complete-full-chain/completion-audit/field_complete_full_chain_completion_audit.json
```

```sh
git diff --check -- docs/plans/2026-05-10-actionable-regime-confidence-todo.md docs/experiments/actionable-regime-confidence/runs/20260510T221112-codex-field-complete-full-chain
```

Audit decision:
The requested regime-confidence objective is complete: every required regime has calibrated 95%+ evidence. The remaining open Board B edge gate blocks trade-usable promotion only; it does not invalidate the Board A confidence result.
