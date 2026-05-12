# Prompt-to-Artifact Completion Audit

- User request: raise every regime to 95% confidence and validate across other markets/timeframes.
- Artifact produced: source-backed MainRegimeV2 root gate over two market families and 15m/1h timeframes.
- Thresholds relaxed: false.
- Runtime code changed: false.
- Predictor leakage guard: `future_*` and `target_*` predictor columns blocked; target columns are labels only.
- Trade usable: false.
- Result: `partial_for_MainRegimeV2_source_backed_roots`; missing roots: BullExpansion, BearExpansion, Consolidation, TransitionRecovery, Manipulation.
- Completion judgment: not complete for the full user objective unless every source-backed root except residual passes and Manipulation has direct required inputs.
