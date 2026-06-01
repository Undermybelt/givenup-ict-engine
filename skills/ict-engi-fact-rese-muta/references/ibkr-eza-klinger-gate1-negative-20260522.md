# IBKR Klinger Gate 1 negatives - 2026-05-22/23

Use under `ict-engi-fact-rese-muta` when rotating public volume-flow/Klinger
families through real IBKR provider rows and Auto-Quant material lanes.

## EZA run

- Root:
  `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260522T181328+0800-codex-ibkr-eza-klinger-volume-flow-1m-gate1-v1`
- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260522T181119+0800-codex-ibkr-eza-klinger-volume-flow-1m-gate1.claim`
- Branch:
  `VolumeFlowExpansion -> SouthAfricaEtfKlingerVolumeFlow ->
  klinger_volume_flow_continuation ->
  ibkr_eza_klinger_volume_flow_1m_gate1_v1`

## EZA result

Real IBKR provider fetches succeeded for `1m/5m/15m/30m/1h/4h/1d`, strategy
compile succeeded, and Auto-Quant material batch, dispatch, and rank all exited
`0`. Branch fields were preserved and `local_cache_replay=false`.

Exact `1m` rank rows were all raw negative and below practical density:

- `kvo_quality`: `13` trades, `0.433333/day`, raw `-0.09%`, `5bps=-1.39%`
- `kvo_reclaim`: `28` trades, `0.933333/day`, raw `-0.66%`, `5bps=-3.46%`
- `kvo_balanced`: `20` trades, `0.666667/day`, raw `-0.32%`, `5bps=-2.32%`
- `kvo_dense`: `26` trades, `0.866667/day`, raw `-0.65%`, `5bps=-3.25%`

Decision: `drop_gate1_no_exact_1m_5bps_density_survivor`.

## MCL 202607 run

- Root:
  `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260523T012658+0800-codex-ibkr-mcl202607-klinger-volume-flow-1m-mtf-gate1-v1`
- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T012658+0800-codex-ibkr-mcl202607-klinger-volume-flow-1m-mtf-gate1.claim`
- Branch:
  `VolumeFlowExpansion -> KlingerVolumeFlow ->
  ibkr_mcl202607_klinger_volume_flow_1m_mtf_gate1_v1`

## MCL 202607 result

Retained-real IBKR ladder rows were present for `1m/5m/15m/30m/1h/4h/1d`, and
strategy compile, Auto-Quant material batch, dispatch, and rank all exited `0`.
Branch fields were preserved and `local_cache_replay=false`.

Exact `1m` rows failed the hard `5bps/side` origin gate:

- `kvo_quality`: `25` trades, `2.777778/day`, raw `+1.18%`, `2bps=+0.18%`,
  `5bps=-1.32%`
- `kvo_reaccel`: `73` trades, `8.111111/day`, raw `+1.70%`,
  `2bps=-1.22%`, `5bps=-5.60%`
- `kvo_balanced`: `85` trades, `9.444444/day`, raw `+1.03%`,
  `2bps=-2.37%`, `5bps=-7.47%`
- `kvo_dense`: `106` trades, raw `-0.51%`, `5bps=-11.11%`

Several `15m/30m/1h/4h` sibling rows survived `5bps/side`, but those are
observation only for a `1m`-origin lane. They do not authorize Pre-Bayes, BBN,
CatBoost, or execution-tree handoff for the failed exact `1m` root.

Decision: `drop_gate1_no_origin_5bps_density_survivor`.

## Lesson

A clean provider/AQ wrapper run is still a Gate 1 stop when the exact `1m` root
is raw negative or lacks `5bps/side` practical density. Do not downstream,
simulate-admit, or add overlays to rescue the exact `EZA/1m/KlingerVolumeFlow`
or `MCL/1m/KlingerVolumeFlow` root. Higher-timeframe Klinger positives should
be preserved as sibling observation evidence; opening one as an exact lane needs
a fresh claim, exact-timeframe Gate 1, and its own downstream decision.
