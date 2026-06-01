# TradingView public strategy absorption for ICT Engine

Use when Board B / profit-factor work asks to mine public TradingView strategies and absorb reusable factor shapes into the provider -> Auto-Quant -> BBN -> CatBoost -> execution-tree chain.

## Workflow

1. Search TradingView public strategy listings with strategy/open-source filters first.
2. Prefer source-visible strategies for detailed feature extraction; if source is not visible, absorb only high-level public description patterns.
3. Do not paste or port Pine source verbatim into the repo. Treat public code as a research reference and implement clean-room strategy material.
4. Convert each absorbed idea into a regime-rooted branch shape before runtime work:

```text
<main_regime> -> <sub_regime> -> <sub_sub_regime_or_profit_factor> -> <profit_factor>
```

5. Preserve branch fields in material JSON and rank artifacts before running downstream admission:

- `branch_path`
- `regime_profit_branch_path`
- `main_regime`
- `sub_regime`
- `sub_sub_regime_or_profit_factor`
- `profit_factor`
- `provider`

6. For bridge-gap / OU-drag blockers, prioritize public strategy shapes that combine independent directional evidence rather than adding another weak confirmation to the same breakout packet.

## High-value absorbed shapes

### JOAT-style market architecture confluence

Observed from TradingView public/open-source JOAT strategy descriptions and source-visible strategy pages.

Useful branch shape:

```text
RangeConsolidation -> ArchitectureConfluence -> joat_pressure_liquidity_bos -> aureate_architecture_confluence_v1
```

Clean-room feature stack:

- Regime: ATR ratio vs ATR baseline, balance width ratio, multi-window ROC pressure, persistence before regime flip, exhaustion blocks entries.
- Structure: confirmed pivot BOS, EMA fast/slow orientation, close relative to fast EMA, optional completed-HTF bias only.
- Pressure: ROC composite over fast/medium/slow/macro windows, smoothed and thresholded by its own volatility.
- Liquidity: upper/lower body anchors, touch density, sweep failure beyond anchor by ATR shelf depth, relative volume floor.
- Risk: structural or ATR stop, R-multiple target, ATR trail, cooldown, exit on exhaustion or opposite BOS.

Why it matters: this shape targets directional bridge-gap widening by requiring regime, structure, pressure, and liquidity to agree before participation.

### Session/range compression breakout

Sources include public Asian Box / Inside Day style strategy descriptions.

Useful branch shape:

```text
RangeConsolidation -> SessionCompression -> session_box_breakout -> session_compression_expansion_v1
```

Clean-room features: range box high/low, low-volatility session, breakout after participation window opens, ATR/volume confirmation, failed-breakout guard.

### SMC/ICT sweep + MSS + FVG stack

Use only from public descriptions unless source-visible.

Useful branch shape:

```text
RangeConsolidation -> LiquidityTransition -> sweep_mss_fvg -> ict_sweep_mss_fvg_expansion_v1
```

Clean-room features: prior swing liquidity sweep, reclaim/reject close, market structure shift, optional fair-value gap retest, session gate.

## Pitfalls

- Do not treat popularity as profitability evidence. It is only idea sourcing.
- Do not count a visible Pine source page as permission to copy strategy code into runtime. Preserve license notes and implement clean-room concepts.
- If a public concept lacks first-class regime root or provider provenance, stop at candidate-pack/material stage; do not claim downstream handoff.
- For current bridge-gap blockers, a light MACD-style confirmation may improve AQ metrics but fail to move downstream BBN/execution. Prefer confluence designs that change the actual selected direction probability and bridge separation.
