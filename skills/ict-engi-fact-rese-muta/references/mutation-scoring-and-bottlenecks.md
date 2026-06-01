Absorbed from skill: ict-engi-fact-muta-optm

This reference stores the detailed scoring anatomy and bottleneck findings for ict-engine factor mutation work.

Key contents preserved:
- composite_score vs mechanical_mutation_score distinction
- expansion_manipulation-specific weighting
- shrink_weight / credibility bottleneck behavior
- need for evaluate_expansion_preview=true in serious studies
- hardcoded-parameter preview-scoring bug and fix pattern
- evidence that structure_ict param search was exhausted under fair isolated runs
- structural next steps: evidence quality, gate uplift, bridge-gap work

Original narrow skill archived after consolidation.

--- PRESERVED HIGHLIGHTS ---

- ExpansionManipulation mutation scores are not governed by the generic composite formula.
- `evaluate_expansion_preview=false` can zero out a large fraction of the score surface.
- A preview scorer hardcoded to default params can falsely make defaults look globally optimal.
- Once isolated experiments still re-select defaults, stop brute-force sweeps and move to structural changes.
