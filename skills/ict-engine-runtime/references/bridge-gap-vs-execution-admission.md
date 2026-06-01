# Bridge gap vs execution admission

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use when a regime-rooted Auto-Quant branch has passed BBN/CatBoost wiring but `workflow-status` or `execution_tree_trace.json` still reports `bridge_needs_confirmation`, `transition_guardrail`, or `observe`.

## Key lesson

Clearing the bridge gap is not the same as execution admission.

There are at least three separate gates:

1. Pre-Bayes bridge gate
   - Source: `workflow_snapshot_runtime.rs`
   - Default threshold: `ICT_ENGINE_BRIDGE_GAP_CLEAR_THRESHOLD=0.12`
   - If `pre_bayes_gate_status=pass_hard` but `pre_bayes_bridge_probability_gap < threshold`, workflow reports `bridge_needs_confirmation`.

2. Transition / temporal guardrail
   - Source: `application/belief/execution_temporal_controls.rs`
   - Default threshold: `ICT_ENGINE_TRANSITION_HAZARD_BLOCK_THRESHOLD=0.60`
   - If `hybrid_transition_hazard >= threshold`, `pda_hybrid_alignment=false`, or duration is too short, execution tree can force:
     - `branch=transition_guardrail`
     - `execution_bias=guarded`
     - `gate_status=observe`

3. Execution readiness gate
   - Source: `domain/execution/gates.rs`
   - Thresholds:
     - `EXECUTION_GATE_READY=0.65`
     - `EXECUTION_GATE_OBSERVE=0.45`
   - `execution_readiness < 0.45` gives `execution_blocked`; `0.45..0.65` gives observe/passive, not actionable execution.

## Probe pattern

Work in copied state only:

```bash
cp -R "$STATE" "$STATE.bridge_probe"
ICT_ENGINE_BRIDGE_GAP_CLEAR_THRESHOLD=0.04 \
ICT_ENGINE_TRANSITION_HAZARD_BLOCK_THRESHOLD=0.70 \
  ict-engine analyze --symbol "$SYM" --state-dir "$STATE.bridge_probe" --agent
ict-engine workflow-status --symbol "$SYM" --state-dir "$STATE.bridge_probe" --refresh --agent
```

Then inspect `state/<SYM>/execution_tree_trace.json` under `output`:

- `branch`
- `gate_status`
- `execution_bias`
- `decision_hint`
- `consumer_reason`
- `path_ranker_score_visible_to_execution_tree`
- `path_ranker_score_used_by_execution_tree`
- `path_ranker_model_family`
- `ranker_validation_ready`

## Interpretation

- `branch=fill_viable` with `gate_status=observe` and `execution_bias=passive` means bridge/transition guardrail was reduced, but execution is still not actionable.
- If `decision_hint=execution_observe_with_medium_prediction`, the next blocker is execution strength, not BBN/CatBoost wiring.
- If real provider frames change the active regime or branch path, ranker can become `ready` but not visible/used for the current branch. Do not claim the original branch was consumed.
- If `pre_bayes=pass_neutralized` or `observe_only`, lowering bridge threshold is not enough; current market/regime evidence no longer supports the branch.

## Practical next move

Do not keep loosening thresholds to force execution. Instead train/select a branch that improves:

- `completion_pressure`
- `evidence_quality`
- `reversion_speed`
- `execution_readiness >= 0.45` for return-to-duty/live-plane admission; target
  `>= 0.65` only for the stronger `execution_ready` class
- no `pda_hybrid_alignment=false`
- transition hazard below the configured block threshold

Only call it executable when `execution_tree_trace.json` shows a non-guarded branch with actionable gate/bias, not merely when `bridge_needs_confirmation` disappears.
