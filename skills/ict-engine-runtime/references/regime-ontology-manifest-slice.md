# Regime ontology manifest slice

Use when implementing the high-confidence regime classifier / expert-bank chain in ICT Engine.

## Trigger

User asks for `R2: Regime ontology manifest`, high-confidence regime labels, one-vs-rest regime experts, or machine-readable regime ontology before feature building/training.

## Files

- `scripts/research/regime_ontology_manifest.py`
- `scripts/research/tests/test_regime_ontology_manifest.py`
- Plan board: `docs/plans/2026-05-09-regime-classifier-research-and-99-confidence-todo.md`

## Expected manifest shape

Outputs:
- `regime_ontology_manifest.json`
- `regime_expert_bank_manifest.jsonl`

Counts:
- primary: 5
- secondary: 16
- dimension: 24
- transition: 8
- total experts: 53

Primary labels:
- `TrendExpansion`
- `RangeConsolidation`
- `ExtremeStress`
- `ReversalBrewing`
- `Unknown`

Secondary labels:
- `BullTrendAcceleration`
- `BearTrendAcceleration`
- `BullTrendExhaustion`
- `BearTrendExhaustion`
- `TightRange`
- `WideRange`
- `Accumulation`
- `Distribution`
- `VolatilitySpike`
- `LiquidityCrunch`
- `PanicSelling`
- `PanicBuying`
- `TrendFatigue`
- `SentimentExtreme`
- `StructureBreakdown`
- `Unknown`

Dimension labels:
- volatility: `LowVol`, `NormalVol`, `ElevatedVol`, `CrisisVol`, `Unknown`
- liquidity: `HighLiquidity`, `NormalLiquidity`, `ThinLiquidity`, `Unknown`
- structure: `Trending`, `MeanReverting`, `Ranging`, `Accumulation`, `Distribution`, `Breakout`, `Breakdown`, `Unknown`
- behavior: `Crowding`, `Exhaustion`, `FOMO`, `Capitulation`, `RiskOn`, `RiskOff`, `Neutral`

Transition labels start with 8 coarse transition experts. Keep as transition hazard evidence, not direct trade signal.

## Required fields per expert

- `label_id`
- `level`: primary / secondary / dimension / transition
- `parent_label`
- `positive_definition`
- `negative_definition`
- `required_features`
- `allowed_data_sources`
- `min_support`
- `target_coverage`
- `abstain_policy`
- `promotion_gates`

`Unknown` and `Neutral` must be abstain/fallback classes. Do not promote them into directional advice.

## TDD / validation

First red should fail on missing `regime_ontology_manifest` module.

Target test:

```bash
python3 -m unittest scripts/research/tests/test_regime_ontology_manifest.py -v
```

Expected after green: 4 tests OK.

Full research sidecar suite:

```bash
python3 -m unittest discover -s scripts/research/tests -p 'test_*.py'
```

Observed after this slice: 57 tests OK.

## Pitfalls

- Do not hardwire 95/99 confidence logic into the ontology. The ontology is a manifest/contract; calibration, conformal sets, payoff utility, and BBN evidence value arrive in later slices.
- Keep implementation as sidecar Python first. Do not modify Rust runtime until sidecar evidence passes.
- Update the plan board acceptance checkboxes immediately after tests pass.
- Before committing, run `git status --short`; preserve unrelated dirty edits such as Rust files changed by other agents.
