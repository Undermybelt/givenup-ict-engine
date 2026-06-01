# Execution gate readiness diagnostics

Session lesson from an ict-engine options/profit-factor iteration where Auto-Quant, real-trade feedback, CatBoost/path-ranker, and exact branch parity all passed, but closed-loop admission remained fail-closed.

## Durable pattern

When a branch reaches tree visibility but `closed_loop_branch_admission.status = fail_closed`, do not keep blindly sweeping timeframes. First split the downstream gates:

1. Verify exact branch parity: `closed_loop_branch_admission.path_id` must equal the tested `regime_profit_branch_path`.
2. Verify sample maturity: `raw_scored_mature`, `production_validation`, and `observation_validation` should meet the 30-row gate.
3. Verify path-ranker runtime: `runtime_selection`, `runtime_source`, `score_model_family`, and `score_source`.
4. Only then inspect execution gate features from `report.supporting.execution_artifact.features`.

## Execution gate contract observed

Source files:

- `src/domain/execution/gates.rs`
- `src/domain/execution/score.rs`
- `src/application/execution/artifact.rs`

Thresholds:

- `execution_ready`: readiness >= 0.65
- `execution_observe_only`: readiness >= 0.45 and < 0.65
- `execution_blocked`: readiness < 0.45

Readiness formula:

```text
readiness = 0.50 * execution_score
          + 0.30 * evidence_quality
          + 0.20 * reversion_speed
          - 0.20 * abs(overextension_distance)
```

Spectral penalty only applies when both are true:

```text
spectral_entropy > 0.80 AND dominant_cycle_energy < 0.15
```

If spectral entropy is low and dominant-cycle energy is healthy, do not blame spectral penalty.

## Diagnostic recipe

After `analyze`, read:

```text
report.supporting.execution_artifact.hard_gate_status
report.supporting.execution_artifact.features.execution_readiness
report.supporting.execution_artifact.features.execution_score
report.supporting.execution_artifact.features.prediction_score
report.supporting.execution_artifact.features.execution_edge_share
report.supporting.execution_artifact.features.evidence_quality
report.supporting.execution_artifact.features.overextension_distance
report.supporting.execution_artifact.features.reversion_speed
report.supporting.execution_artifact.features.dominant_cycle_energy
report.supporting.execution_artifact.features.spectral_entropy
```

Then compute the gap to return-to-duty and, separately, the gap to the stronger
ready class:

```text
return_to_duty_shortfall = max(0.45 - execution_readiness, 0)
ready_class_shortfall = max(0.65 - execution_readiness, 0)
required_evidence_if_only_evidence_changes = (0.65 - 0.50*execution_score - 0.20*reversion_speed + 0.20*abs(overextension_distance)) / 0.30
required_execution_score_if_only_execution_changes = (0.65 - 0.30*evidence_quality - 0.20*reversion_speed + 0.20*abs(overextension_distance)) / 0.50
```

Use `0.45` as the closed-loop return-to-duty/live-plane admission floor for
cost-positive same-root candidates. Use `0.65` only when diagnosing the stronger
`execution_ready` class. Do not terminalize an otherwise valid same-root branch
only because it is in the `0.45..0.65` observe/passive band.

## Session example

Best retained-cache probe:

```text
symbol branch: TrendExpansion -> IBKRMultiSymbol -> gap_go_5m -> gap_003_confirm6_target015_stop015_hold24
input: XLK 5m/5m/5m with --apply-regime-bundle-bbn-soft-evidence
execution_readiness = 0.638865
ready_threshold = 0.65
shortfall = 0.011135
execution_score = 0.710542
evidence_quality = 0.944786
overextension_distance = 0.0
reversion_speed = 0.000791
spectral_entropy = 0.204
dominant_cycle_energy = 0.713
```

Interpretation:

- No spectral penalty.
- No overextension penalty.
- Exact branch parity passed.
- Path-ranker maturity passed (`48/30`).
- Execution gate still observe-only because execution_score/evidence_quality are just short of ready.

## Correct next moves

Valid:

- Add fresh provider-backed observations that can raise evidence quality or execution score.
- Add a source-backed execution overlay that legitimately improves completion pressure, liquidity absorption, or evidence quality.
- Review the execution-readiness contract if the ready threshold/formula is judged too conservative for this class.

Invalid:

- Claim live-readiness from path-ranker maturity alone.
- Continue blind timeframe sweeps on the same retained cache after the best probe is within a fixed execution-readiness shortfall.
- Describe provider-window timeouts as factor failures.
